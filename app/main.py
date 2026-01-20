"""
标题: Main
说明: FastAPI 主应用程序，提供 Whisper 语音识别 REST API 接口
时间: 2026-01-14
@author: zhoujunyu
"""

import os
import time
import uuid
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware

from .config import settings
from .models import (
    TranscribeResponse, 
    TranscribeUrlRequest, 
    TranscribeDetailResponse,
    HealthResponse
)
from .services.whisper_service import whisper_service


def setup_logging():
    """
    配置日志系统
    同时输出到控制台和文件
    """
    # 创建日志目录
    log_dir = Path("./logs")
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # 日志格式
    log_format = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # 根日志配置
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # 文件处理器 - 按日期滚动
    log_file = log_dir / f"whisper_api_{datetime.now().strftime('%Y%m%d')}.log"
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # 清除已有处理器并添加新处理器
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    return logging.getLogger(__name__)


# 初始化日志
logger = setup_logging()


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    请求日志中间件
    记录每个请求的详细信息
    """
    
    async def dispatch(self, request: Request, call_next):
        """
        处理请求并记录日志
        """
        # 生成请求ID
        request_id = str(uuid.uuid4())[:8]
        start_time = time.time()
        
        # 记录请求开始
        logger.info(f"[{request_id}] --> {request.method} {request.url.path}")
        
        # 处理请求
        try:
            response = await call_next(request)
            
            # 计算处理时间
            process_time = time.time() - start_time
            
            # 记录请求完成
            logger.info(
                f"[{request_id}] <-- {response.status_code} "
                f"| 耗时: {process_time:.2f}s"
            )
            
            # 添加响应头
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.3f}s"
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"[{request_id}] <-- 500 ERROR | 耗时: {process_time:.2f}s | {str(e)}"
            )
            raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    在启动时预加载模型（可选）
    """
    logger.info("=" * 60)
    logger.info("Whisper API 服务启动 (Faster-Whisper)")
    logger.info(f"模型: {settings.MODEL_NAME}")
    logger.info(f"设备: {settings.DEVICE}")
    logger.info(f"计算类型: {settings.COMPUTE_TYPE}")
    logger.info(f"CPU 线程数: {settings.CPU_THREADS}")
    logger.info(f"临时目录: {settings.TEMP_DIR}")
    logger.info(f"模型目录: {settings.MODEL_DIR}")
    logger.info(f"日志目录: ./logs")
    logger.info("=" * 60)
    
    # 可选：预加载模型（取消注释以启用）
    # logger.info("预加载模型中...")
    # whisper_service.model
    # logger.info("模型预加载完成")
    
    yield
    
    logger.info("=" * 60)
    logger.info("Whisper API 服务关闭")
    logger.info("=" * 60)


# 创建 FastAPI 应用
app = FastAPI(
    title="Whisper API",
    description="基于 OpenAI Whisper 的语音识别 API 服务",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加请求日志中间件
app.add_middleware(RequestLoggingMiddleware)


@app.get("/", response_model=HealthResponse)
async def health_check():
    """
    健康检查接口
    
    返回服务状态和当前配置信息
    """
    return HealthResponse(
        status="ok",
        message="Whisper API 正在运行",
        model=settings.MODEL_NAME,
        device=settings.DEVICE
    )


@app.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_file(
    file: UploadFile = File(..., description="要转录的音频文件"),
    language: Optional[str] = Form(None, description="语言代码（如 'zh', 'en'），留空自动检测")
):
    """
    文件上传转录接口
    
    上传音频文件进行语音识别，返回转录文本
    
    支持的格式：mp3, wav, m4a, flac, ogg, wma, aac, opus, webm, mp4
    """
    # 验证文件类型
    if not file.filename:
        raise HTTPException(status_code=400, detail="未提供文件名")
    
    if not settings.is_allowed_file(file.filename):
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的文件格式。支持的格式：{', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    # 获取文件扩展名
    ext = file.filename.rsplit(".", 1)[1].lower()
    
    # 保存上传的文件到临时目录
    temp_path = settings.TEMP_DIR / f"upload_{os.getpid()}.{ext}"
    
    try:
        # 记录文件信息
        file_size_mb = 0
        logger.info(f"📥 接收文件: {file.filename}")
        
        # 保存文件
        content = await file.read()
        file_size_mb = len(content) / 1024 / 1024
        
        # 检查文件大小
        if len(content) > settings.MAX_FILE_SIZE:
            logger.warning(f"⚠️ 文件过大: {file_size_mb:.2f}MB (最大 {settings.MAX_FILE_SIZE // 1024 // 1024}MB)")
            raise HTTPException(
                status_code=413, 
                detail=f"文件过大。最大允许 {settings.MAX_FILE_SIZE // 1024 // 1024}MB"
            )
        
        with open(temp_path, "wb") as f:
            f.write(content)
        
        logger.info(f"💾 文件已保存: {file.filename} ({file_size_mb:.2f}MB)")
        
        # 获取音频时长
        duration = whisper_service.get_audio_duration(str(temp_path))
        if duration > 0:
            logger.info(f"⏱️ 音频时长: {duration:.1f}秒")
        
        # 执行转录
        transcribe_start = time.time()
        logger.info(f"🎤 开始转录... (语言: {language or '自动检测'})")
        
        result = whisper_service.transcribe(str(temp_path), language)
        
        transcribe_time = time.time() - transcribe_start
        text_length = len(result.get("text", ""))
        detected_lang = result.get("language", "unknown")
        
        logger.info(f"✅ 转录完成 | 耗时: {transcribe_time:.1f}s | 语言: {detected_lang} | 文本长度: {text_length}字符")
        
        # 计算实时率 (RTF)
        if duration > 0:
            rtf = transcribe_time / duration
            logger.info(f"📊 实时率(RTF): {rtf:.2f}x (1分钟音频需要{rtf:.1f}分钟处理)")
        
        return TranscribeResponse(
            success=True,
            text=result.get("text", "").strip(),
            language=result.get("language"),
            duration=duration if duration > 0 else None
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"转录失败: {e}", exc_info=True)
        return TranscribeResponse(
            success=False,
            text="",
            error=str(e)
        )
    finally:
        # 清理临时文件
        if temp_path.exists():
            temp_path.unlink()
            logger.info("临时文件已清理")


@app.post("/transcribe/url", response_model=TranscribeResponse)
async def transcribe_url(request: TranscribeUrlRequest):
    """
    URL 转录接口
    
    通过 URL 提交音频进行语音识别
    
    服务会自动下载音频文件并进行转录
    """
    try:
        logger.info(f"URL 转录请求: {request.url}")
        
        # 下载并转录
        result = await whisper_service.transcribe_from_url(
            request.url, 
            request.language
        )
        
        return TranscribeResponse(
            success=True,
            text=result.get("text", "").strip(),
            language=result.get("language")
        )
        
    except Exception as e:
        logger.error(f"URL 转录失败: {e}", exc_info=True)
        return TranscribeResponse(
            success=False,
            text="",
            error=str(e)
        )


@app.post("/transcribe/detail", response_model=TranscribeDetailResponse)
async def transcribe_file_detail(
    file: UploadFile = File(..., description="要转录的音频文件"),
    language: Optional[str] = Form(None, description="语言代码（如 'zh', 'en'），留空自动检测")
):
    """
    详细转录接口（带时间戳）
    
    返回包含时间戳信息的详细转录结果
    """
    # 验证文件类型
    if not file.filename:
        raise HTTPException(status_code=400, detail="未提供文件名")
    
    if not settings.is_allowed_file(file.filename):
        raise HTTPException(
            status_code=400, 
            detail=f"不支持的文件格式。支持的格式：{', '.join(settings.ALLOWED_EXTENSIONS)}"
        )
    
    ext = file.filename.rsplit(".", 1)[1].lower()
    temp_path = settings.TEMP_DIR / f"upload_{os.getpid()}.{ext}"
    
    try:
        content = await file.read()
        
        if len(content) > settings.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413, 
                detail=f"文件过大。最大允许 {settings.MAX_FILE_SIZE // 1024 // 1024}MB"
            )
        
        with open(temp_path, "wb") as f:
            f.write(content)
        
        # 获取音频时长
        duration = whisper_service.get_audio_duration(str(temp_path))
        
        # 执行转录
        result = whisper_service.transcribe(str(temp_path), language)
        
        # 提取片段信息
        segments = []
        for seg in result.get("segments", []):
            segments.append({
                "id": seg.get("id", 0),
                "start": seg.get("start", 0),
                "end": seg.get("end", 0),
                "text": seg.get("text", "").strip()
            })
        
        return TranscribeDetailResponse(
            success=True,
            text=result.get("text", "").strip(),
            language=result.get("language"),
            duration=duration if duration > 0 else None,
            segments=segments
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"详细转录失败: {e}", exc_info=True)
        return TranscribeDetailResponse(
            success=False,
            text="",
            error=str(e)
        )
    finally:
        if temp_path.exists():
            temp_path.unlink()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True
    )
