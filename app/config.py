"""
标题: Config
说明: 应用配置管理类，包含 Whisper 模型配置和服务器配置
时间: 2026-01-14
@author: zhoujunyu
"""

import os
from pathlib import Path


class Settings:
    """
    应用配置类
    管理 Whisper API 的所有配置项
    """
    
    # Faster-Whisper 模型配置
    MODEL_NAME: str = os.getenv("WHISPER_MODEL", "small")
    """Whisper 模型名称：tiny, base, small, medium, large"""
    
    DEVICE: str = os.getenv("WHISPER_DEVICE", "cpu")
    """运行设备：cpu 或 cuda"""
    
    COMPUTE_TYPE: str = os.getenv("WHISPER_COMPUTE_TYPE", "int8")
    """计算类型：int8（CPU快速）、float16（GPU）、float32（兼容）"""
    
    CPU_THREADS: int = int(os.getenv("WHISPER_CPU_THREADS", "4"))
    """CPU 线程数，建议设置为 CPU 核心数"""
    
    MODEL_DIR: Path = Path(os.getenv("WHISPER_MODEL_DIR", "./models"))
    """模型下载/存放目录"""
    
    # 本地模型路径（如果设置，直接使用此路径加载模型）
    # 例如: ./models/faster-whisper-small
    LOCAL_MODEL_PATH: str = os.getenv("WHISPER_LOCAL_MODEL_PATH", "")
    
    # 服务器配置
    HOST: str = os.getenv("API_HOST", "0.0.0.0")
    """服务监听地址"""
    
    PORT: int = int(os.getenv("API_PORT", "8000"))
    """服务监听端口"""
    
    # 文件配置
    TEMP_DIR: Path = Path(os.getenv("TEMP_DIR", "./temp"))
    """临时文件存储目录"""
    
    MAX_FILE_SIZE: int = int(os.getenv("MAX_FILE_SIZE", str(100 * 1024 * 1024)))  # 100MB
    """最大上传文件大小（字节）"""
    
    # 支持的音频格式
    ALLOWED_EXTENSIONS: set = {
        "mp3", "wav", "m4a", "flac", "ogg", 
        "wma", "aac", "opus", "webm", "mp4"
    }
    """支持的音频文件扩展名"""
    
    def __init__(self):
        """
        初始化配置
        确保临时目录和模型目录存在
        """
        self.TEMP_DIR.mkdir(parents=True, exist_ok=True)
        self.MODEL_DIR.mkdir(parents=True, exist_ok=True)
    
    def is_allowed_file(self, filename: str) -> bool:
        """
        检查文件扩展名是否允许
        
        Args:
            filename: 文件名
            
        Returns:
            bool: 是否允许上传该文件类型
        """
        if "." not in filename:
            return False
        ext = filename.rsplit(".", 1)[1].lower()
        return ext in self.ALLOWED_EXTENSIONS


# 全局配置实例
settings = Settings()
