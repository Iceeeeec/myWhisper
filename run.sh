#!/bin/bash
# ========================================
# 标题: Whisper API 启动脚本 (Linux/Mac)
# 说明: 启动 Whisper API 服务
# 时间: 2026-01-14
# @author: zhoujunyu
# ========================================

echo "=========================================="
echo "  Whisper API 服务启动脚本"
echo "=========================================="
echo

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未找到 Python3，请先安装 Python 3.9+"
    exit 1
fi

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "[信息] 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
echo "[信息] 激活虚拟环境..."
source venv/bin/activate

# 安装依赖
echo "[信息] 检查依赖..."
pip install -r requirements.txt -q

# 启动服务
echo
echo "[信息] 启动 Whisper API 服务..."
echo "[信息] 访问 http://localhost:8000/docs 查看 API 文档"
echo

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
