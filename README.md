# Whisper API Service

[![Python](https://img.shields.io/badge/Python-3.9%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104.0%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![Docker](https://img.shields.io/badge/Docker-Supported-2496ED.svg)](https://www.docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

基于 OpenAI Whisper (Faster-Whisper) 的高性能语音识别 REST API 服务。专为生产环境设计，支持多线程并发推理和 Docker 容器化部署。

## ✨ 功能特性

- 🚀 **高性能**: 基于 `faster-whisper` (CTranslate2)，比原版快 4-8 倍
- 🧵 **多线程支持**: 充分利用多核 CPU 进行并行推理
- 🐳 **Docker 就绪**: 提供完整的 Docker 和 Docker Compose 部署方案
- 📝 **详细转录**: 支持生成带时间戳的精确转录结果
- 🌐 **多语言**: 自动检测并支持多种语言识别
- 🔌 **标准 API**: 提供文件上传和 URL 下载两种转录接口

## 🛠️ 技术栈

- **核心引擎**: [Faster-Whisper](https://github.com/SYSTRAN/faster-whisper) (small 模型)
- **Web 框架**: FastAPI + Uvicorn (异步并发)
- **运行环境**: Python 3.9+ / Docker
- **音频处理**: FFmpeg

## 🚀 快速开始

### 方式一：Docker Compose (推荐)

最简单的部署方式，无需配置本地环境。

```bash
# 1. 构建并启动服务
docker-compose up -d

# 2. 查看日志
docker-compose logs -f
```

> **注意**: 首次启动会自动下载 Whisper 模型 (约 500MB)，请耐心等待。

### 方式二：本地运行

#### Windows

```bash
# 双击运行脚本
.\run.bat
```

#### Linux/Mac

```bash
chmod +x run.sh
./run.sh
```

## ⚙️ 配置说明

项目支持通过环境变量进行配置，特别针对 **8核服务器** 进行了优化默认设置。

| 环境变量               | 默认值  | 说明                                                   |
| :--------------------- | :------ | :----------------------------------------------------- |
| `WHISPER_MODEL`        | `small` | 模型大小 (tiny, base, small, medium, large)            |
| `WHISPER_DEVICE`       | `cpu`   | 运行设备 (cpu, cuda)                                   |
| `WHISPER_CPU_THREADS`  | `4`     | **关键**: 推理使用的 CPU 线程数 (建议设置为物理核心数) |
| `WHISPER_COMPUTE_TYPE` | `int8`  | 计算精度 (int8 为 CPU 推荐，速度最快)                  |
| `API_PORT`             | `8000`  | 服务端口                                               |

### 性能优化建议

对于 8 核服务器，建议配置：

- `WHISPER_CPU_THREADS=6` (留 2 核给系统和 Web 服务)
- `WHISPER_COMPUTE_TYPE=int8` (CPU 模式下最佳性能)

## 📚 API 接口文档

启动后访问: `http://localhost:8000/docs`

### 1. 健康检查

```bash
curl http://localhost:8000/
```

### 2. 文件上传转录

```bash
curl -X POST "http://localhost:8000/transcribe" \
  -F "file=@audio.mp3" \
  -F "language=zh"
```

### 3. URL 转录

```bash
curl -X POST "http://localhost:8000/transcribe/url" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com/audio.mp3", "language": "zh"}'
```

## 📋 支持格式

支持所有 FFmpeg 兼容格式：
`mp3`, `wav`, `m4a`, `flac`, `ogg`, `wma`, `aac`, `opus`, `webm`, `mp4`

## 👤 作者

- **zhoujunyu**
- 2026-01-14
