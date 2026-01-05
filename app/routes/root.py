"""
根路由
"""

from fastapi import APIRouter

router = APIRouter(tags=["Root"])


@router.get("/")
async def root():
    """根端點"""
    return {
        "message": "歡迎使用 Vanna AI Chatbot API",
        "docs": "/docs",
        "health": "/api/health"
    }

