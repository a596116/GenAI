"""
FastAPI 主應用程式
提供 RESTful API 端點供前端調用
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .vanna_client import vanna_client
from .routes import (
    root_router,
    health_router,
    chat_router,
    training_router,
    database_router,
    conversations_router
)

# 配置日誌
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
# 設置 Vanna 相關日誌為 DEBUG 級別以便調試
logging.getLogger('app.vanna_client').setLevel(logging.DEBUG)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """應用程式生命週期管理"""
    # 啟動時執行
    logger.info("正在啟動 Vanna AI Chatbot 後端...")
    
    # 初始化 Vanna 客戶端
    if vanna_client.initialize():
        logger.info("Vanna AI 客戶端初始化成功")
    else:
        logger.warning("Vanna AI 客戶端初始化失敗，某些功能可能無法使用")
    
    yield
    
    # 關閉時執行
    logger.info("正在關閉 Vanna AI Chatbot 後端...")


# 創建 FastAPI 應用實例
app = FastAPI(
    title="Vanna AI Chatbot API",
    description="使用 Vanna AI 和 OpenAI 將自然語言轉換為 SQL 查詢的智能助手",
    version="1.0.0",
    lifespan=lifespan
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生產環境應該限制具體來源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 註冊路由
app.include_router(root_router)
app.include_router(health_router)
app.include_router(chat_router)
app.include_router(training_router)
app.include_router(database_router)
app.include_router(conversations_router)


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.debug
    )
