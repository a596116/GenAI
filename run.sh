#!/bin/bash

# Vanna AI Chatbot 啟動腳本

echo "🚀 正在啟動 Vanna AI Chatbot 後端..."
echo ""

# 檢查虛擬環境
if [ ! -d "venv" ]; then
    echo "❌ 未找到虛擬環境，請先執行: python -m venv venv"
    exit 1
fi

# 檢查 .env 文件
if [ ! -f ".env" ]; then
    echo "⚠️  未找到 .env 文件，請從 .env.example 複製並配置"
    echo "   執行: cp .env.example .env"
    exit 1
fi

# 啟動應用
echo "✅ 正在啟動應用..."
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

echo ""
echo "✨ 應用已啟動！"
echo "📝 API 文檔: http://localhost:8000/docs"
echo "🔍 健康檢查: http://localhost:8000/api/health"

