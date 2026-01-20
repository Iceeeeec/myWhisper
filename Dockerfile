# ========================================
# 标题: Dockerfile
# 说明: Whisper API Docker 镜像配置 (Faster-Whisper)
# 时间: 2026-01-14
# @author: zhoujunyu
# ========================================

FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量避免交互
ENV DEBIAN_FRONTEND=noninteractive
ENV PIP_NO_CACHE_DIR=1

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# 复制应用代码
COPY app/ ./app/

# 创建必要目录
RUN mkdir -p /app/temp /app/models /app/logs

# 模型通过 docker-compose volumes 挂载
# 请先运行 download_model.py 在本地下载模型

# 设置环境变量
ENV WHISPER_MODEL=small
ENV WHISPER_DEVICE=cpu
ENV WHISPER_COMPUTE_TYPE=int8
ENV WHISPER_CPU_THREADS=4
ENV WHISPER_MODEL_DIR=/app/models
ENV API_HOST=0.0.0.0
ENV API_PORT=8000
ENV TEMP_DIR=/app/temp

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
