"""
标题: WhisperService
说明: 基于 Faster-Whisper 的语音识别服务封装类，提供高效音频转文字功能
时间: 2026-01-14
@author: zhoujunyu
"""

import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List

from faster_whisper import WhisperModel
import httpx

from ..config import settings

# 配置日志
logger = logging.getLogger(__name__)


class WhisperService:
    """
    Faster-Whisper 语音识别服务类
    
    基于 CTranslate2 优化，比原版 Whisper 快 4-8 倍
    提供音频文件的语音转文字功能，支持：
    - 本地文件转录
    - URL 音频下载并转录
    - 自动语言检测
    - 多核 CPU 并行处理
    """
    
    _instance: Optional["WhisperService"] = None
    _model: Optional[WhisperModel] = None
    
    def __new__(cls) -> "WhisperService":
        """
        单例模式实现
        确保只有一个服务实例和模型实例
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """
        初始化服务
        注意：模型采用懒加载方式
        """
        pass
    
    def _load_model(self) -> WhisperModel:
        """
        加载 Faster-Whisper 模型（懒加载）
        
        Returns:
            WhisperModel: 加载的模型实例
        """
        if self._model is None:
            logger.info("=" * 50)
            logger.info("🚀 开始加载 Faster-Whisper 模型")
            logger.info(f"   模型名称: {settings.MODEL_NAME}")
            logger.info(f"   运行设备: {settings.DEVICE}")
            logger.info(f"   计算类型: {settings.COMPUTE_TYPE}")
            logger.info(f"   CPU线程数: {settings.CPU_THREADS}")
            logger.info(f"   模型目录: {settings.MODEL_DIR}")
            if settings.LOCAL_MODEL_PATH:
                logger.info(f"   本地模型路径: {settings.LOCAL_MODEL_PATH}")
            logger.info("=" * 50)
            
            # 确定最佳计算类型
            compute_type = settings.COMPUTE_TYPE
            if settings.DEVICE == "cpu" and compute_type == "float16":
                logger.warning("⚠️ CPU 不支持 float16，自动切换为 int8")
                compute_type = "int8"
            
            # 确定模型路径
            # 如果设置了本地模型路径，直接使用
            # 否则使用模型名称（会尝试从 HuggingFace 下载）
            model_path = settings.LOCAL_MODEL_PATH if settings.LOCAL_MODEL_PATH else settings.MODEL_NAME
            
            try:
                # Faster-Whisper 模型加载
                self._model = WhisperModel(
                    model_path,
                    device=settings.DEVICE,
                    compute_type=compute_type,
                    cpu_threads=settings.CPU_THREADS,
                    download_root=str(settings.MODEL_DIR) if not settings.LOCAL_MODEL_PATH else None
                )
                logger.info(f"✅ 模型加载完成，实际计算类型: {compute_type}")
            except Exception as e:
                # 如果 int8 失败，回退到 float32
                logger.warning(f"⚠️ {compute_type} 加载失败: {e}")
                logger.info("🔄 回退使用 float32...")
                self._model = WhisperModel(
                    model_path,
                    device=settings.DEVICE,
                    compute_type="float32",
                    cpu_threads=settings.CPU_THREADS,
                    download_root=str(settings.MODEL_DIR) if not settings.LOCAL_MODEL_PATH else None
                )
                logger.info("✅ 模型加载完成 (float32 模式)")
        
        return self._model
    
    @property
    def model(self) -> WhisperModel:
        """
        获取模型实例
        
        Returns:
            WhisperModel: 模型实例
        """
        return self._load_model()
    
    def transcribe(
        self, 
        audio_path: str, 
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        转录音频文件
        
        Args:
            audio_path: 音频文件路径
            language: 语言代码（可选，如 'zh', 'en'），留空自动检测
            
        Returns:
            Dict: 包含转录结果的字典
                - text: 转录文本
                - language: 检测到的语言
                - segments: 带时间戳的片段列表
        """
        logger.info(f"开始转录: {audio_path}")
        
        # 构建转录参数
        transcribe_options = {
            "beam_size": 5,
            "vad_filter": True,  # 启用 VAD 过滤静音，加速处理
            "vad_parameters": {
                "min_silence_duration_ms": 500
            }
        }
        
        if language:
            transcribe_options["language"] = language
            logger.info(f"指定语言: {language}")
        
        # 执行转录 - Faster-Whisper 返回生成器
        segments_generator, info = self.model.transcribe(
            audio_path, 
            **transcribe_options
        )
        
        # 收集所有片段
        segments: List[Dict[str, Any]] = []
        full_text_parts: List[str] = []
        
        for segment in segments_generator:
            segments.append({
                "id": segment.id,
                "start": segment.start,
                "end": segment.end,
                "text": segment.text.strip()
            })
            full_text_parts.append(segment.text)
        
        full_text = "".join(full_text_parts).strip()
        
        logger.info(f"转录完成，检测语言: {info.language}, 片段数: {len(segments)}")
        
        # 返回与原版 Whisper 兼容的格式
        return {
            "text": full_text,
            "language": info.language,
            "segments": segments,
            "duration": info.duration
        }
    
    async def transcribe_from_url(
        self, 
        url: str, 
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        从 URL 下载音频并转录
        
        Args:
            url: 音频文件 URL
            language: 语言代码（可选）
            
        Returns:
            Dict: 包含转录结果的字典
            
        Raises:
            Exception: 下载失败或转录失败时抛出异常
        """
        logger.info(f"从 URL 下载音频: {url}")
        
        # 从 URL 提取文件扩展名
        url_path = url.split("?")[0]  # 移除查询参数
        ext = url_path.rsplit(".", 1)[-1] if "." in url_path else "mp3"
        
        # 创建临时文件
        temp_path = settings.TEMP_DIR / f"download_{os.getpid()}.{ext}"
        
        try:
            # 下载文件
            async with httpx.AsyncClient() as client:
                response = await client.get(url, follow_redirects=True, timeout=60.0)
                response.raise_for_status()
                
                with open(temp_path, "wb") as f:
                    f.write(response.content)
            
            logger.info(f"下载完成，文件大小: {temp_path.stat().st_size} bytes")
            
            # 转录
            result = self.transcribe(str(temp_path), language)
            
            return result
            
        finally:
            # 清理临时文件
            if temp_path.exists():
                temp_path.unlink()
                logger.info("临时文件已清理")
    
    def get_audio_duration(self, audio_path: str) -> float:
        """
        获取音频文件时长
        
        Args:
            audio_path: 音频文件路径
            
        Returns:
            float: 音频时长（秒）
        """
        try:
            import subprocess
            result = subprocess.run(
                [
                    "ffprobe", "-v", "error", 
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    audio_path
                ],
                capture_output=True,
                text=True
            )
            return float(result.stdout.strip())
        except Exception as e:
            logger.warning(f"无法获取音频时长: {e}")
            return 0.0


# 全局服务实例
whisper_service = WhisperService()
