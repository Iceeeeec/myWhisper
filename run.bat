@echo off
REM ========================================
REM 标题: Whisper API 启动脚本 (Windows)
REM 说明: 启动 Whisper API 服务
REM 时间: 2026-01-14
REM @author: zhoujunyu
REM ========================================

echo ==========================================
echo   Whisper API 服务启动脚本
echo ==========================================
echo.

REM 检查 Python 是否安装
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.9+
    pause
    exit /b 1
)

REM 检查虚拟环境
if not exist "venv" (
    echo [信息] 创建虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
echo [信息] 激活虚拟环境...
call venv\Scripts\activate.bat

REM 安装依赖
echo [信息] 检查依赖...
pip install -r requirements.txt -q

REM 启动服务
echo.
echo [信息] 启动 Whisper API 服务...
echo [信息] 访问 http://localhost:8000/docs 查看 API 文档
echo.

python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

pause
