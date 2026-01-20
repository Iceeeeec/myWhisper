"""
标题: DownloadModel
说明: 离线下载 Faster-Whisper 模型脚本
时间: 2026-01-14
@author: zhoujunyu

使用方法:
1. 在本地电脑运行: python download_model.py
2. 将 models 目录上传到服务器
3. 修改 docker-compose.yml 挂载 models 目录
"""

import os
import sys


def download_model(model_name: str = "small"):
    """
    下载 Faster-Whisper 模型
    
    Args:
        model_name: 模型名称 (tiny, base, small, medium, large)
    """
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        print("错误: 请先安装 faster-whisper")
        print("运行: pip install faster-whisper")
        sys.exit(1)
    
    # 创建 models 目录
    models_dir = os.path.join(os.path.dirname(__file__), "models")
    os.makedirs(models_dir, exist_ok=True)
    
    print("=" * 50)
    print(f"开始下载 Faster-Whisper 模型: {model_name}")
    print(f"保存目录: {models_dir}")
    print("=" * 50)
    print()
    
    try:
        # 下载模型 (使用 int8 量化版本)
        print("正在下载模型文件，请稍候...")
        print("(这可能需要几分钟，取决于网络速度)")
        print()
        
        model = WhisperModel(
            model_name,
            device="cpu",
            compute_type="int8",
            download_root=models_dir
        )
        
        print()
        print("=" * 50)
        print("✅ 模型下载完成!")
        print(f"模型保存在: {models_dir}")
        print()
        print("下一步操作:")
        print("1. 将 models 目录上传到服务器的项目目录下")
        print("2. 修改 docker-compose.yml:")
        print("   volumes:")
        print("     - ./models:/app/models")
        print("3. 重新构建并启动容器")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # 默认下载 small 模型，可以通过命令行参数修改
    model_name = sys.argv[1] if len(sys.argv) > 1 else "small"
    download_model(model_name)
