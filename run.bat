@echo off
REM Vanna AI Chatbot 啟動腳本 (Windows)

echo 🚀 正在啟動 Vanna AI Chatbot 後端...
echo.

REM 檢查虛擬環境
if not exist "venv\" (
    echo ❌ 未找到虛擬環境，請先執行: python -m venv venv
    exit /b 1
)

REM 檢查 .env 文件
if not exist ".env" (
    echo ⚠️  未找到 .env 文件，請從 .env.example 複製並配置
    echo    執行: copy .env.example .env
    exit /b 1
)

REM 啟動應用
echo ✅ 正在啟動應用...
call venv\Scripts\activate.bat
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

echo.
echo ✨ 應用已啟動！
echo 📝 API 文檔: http://localhost:8000/docs
echo 🔍 健康檢查: http://localhost:8000/api/health

