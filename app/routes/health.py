"""
健康檢查路由
"""

import logging
from fastapi import APIRouter, HTTPException, status
from app.models import HealthResponse
from app.vanna_client import vanna_client

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Health"])


@router.get("/api/health", response_model=HealthResponse)
async def health_check():
    """
    健康檢查端點
    
    檢查服務、數據庫連接和 Vanna AI 的狀態
    """
    try:
        # 檢查數據庫連接
        db_connected = vanna_client.test_connection()
        
        # 檢查 Vanna 初始化狀態
        vanna_initialized = vanna_client.is_initialized()
        
        # 判斷整體狀態
        if db_connected and vanna_initialized:
            status_str = "healthy"
        elif db_connected or vanna_initialized:
            status_str = "degraded"
        else:
            status_str = "unhealthy"
        
        return HealthResponse(
            status=status_str,
            database_connected=db_connected,
            vanna_initialized=vanna_initialized
        )
    except Exception as e:
        logger.error(f"健康檢查失敗: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"健康檢查失敗: {str(e)}"
        )

