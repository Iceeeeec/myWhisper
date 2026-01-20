"""
标题: Models
说明: Pydantic 数据模型定义，用于请求和响应的数据验证
时间: 2026-01-14
@author: zhoujunyu
"""

from typing import Optional, List
from pydantic import BaseModel, Field


class TranscribeResponse(BaseModel):
    """
    转录响应模型
    包含转录结果的所有信息
    """
    
    success: bool = Field(
        description="请求是否成功"
    )
    text: str = Field(
        default="",
        description="转录的文本内容"
    )
    language: Optional[str] = Field(
        default=None,
        description="检测到的语言代码"
    )
    duration: Optional[float] = Field(
        default=None,
        description="音频时长（秒）"
    )
    error: Optional[str] = Field(
        default=None,
        description="错误信息（如果失败）"
    )


class TranscribeUrlRequest(BaseModel):
    """
    URL 转录请求模型
    用于通过 URL 提交音频进行转录
    """
    
    url: str = Field(
        description="音频文件的 URL 地址"
    )
    language: Optional[str] = Field(
        default=None,
        description="音频语言代码（如 'zh', 'en'），留空自动检测"
    )


class SegmentInfo(BaseModel):
    """
    转录片段信息模型
    用于返回带时间戳的转录结果
    """
    
    id: int = Field(
        description="片段 ID"
    )
    start: float = Field(
        description="开始时间（秒）"
    )
    end: float = Field(
        description="结束时间（秒）"
    )
    text: str = Field(
        description="片段文本"
    )


class TranscribeDetailResponse(BaseModel):
    """
    详细转录响应模型
    包含时间戳信息的完整转录结果
    """
    
    success: bool = Field(
        description="请求是否成功"
    )
    text: str = Field(
        default="",
        description="完整的转录文本"
    )
    language: Optional[str] = Field(
        default=None,
        description="检测到的语言代码"
    )
    duration: Optional[float] = Field(
        default=None,
        description="音频时长（秒）"
    )
    segments: List[SegmentInfo] = Field(
        default=[],
        description="带时间戳的转录片段列表"
    )
    error: Optional[str] = Field(
        default=None,
        description="错误信息（如果失败）"
    )


class HealthResponse(BaseModel):
    """
    健康检查响应模型
    """
    
    status: str = Field(
        description="服务状态"
    )
    message: str = Field(
        description="状态信息"
    )
    model: str = Field(
        description="当前加载的模型名称"
    )
    device: str = Field(
        description="运行设备（cpu/cuda）"
    )
