"""
訓練路由
"""

import logging
from fastapi import APIRouter, HTTPException, status
from app.models import TrainRequest, TrainResponse
from app.vanna_client import vanna_client

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Training"])


@router.post("/api/train", response_model=TrainResponse)
async def train(request: TrainRequest):
    """
    訓練端點 - 訓練 Vanna AI 模型
    
    可以添加 DDL、文檔或 SQL 範例來訓練模型
    
    Args:
        request: 訓練請求，包含 DDL、文檔或 SQL 範例
        
    Returns:
        TrainResponse: 訓練結果
    """
    try:
        if not vanna_client.is_initialized():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Vanna AI 服務尚未初始化，請稍後再試"
            )
        
        success_count = 0
        messages = []
        
        # 訓練 DDL
        if request.ddl:
            if vanna_client.train_on_ddl(request.ddl):
                success_count += 1
                messages.append("成功添加 DDL 訓練資料")
            else:
                messages.append("添加 DDL 訓練資料失敗")
        
        # 訓練文檔
        if request.documentation:
            if vanna_client.train_on_documentation(request.documentation):
                success_count += 1
                messages.append("成功添加文檔訓練資料")
            else:
                messages.append("添加文檔訓練資料失敗")
        
        # 訓練 SQL
        if request.sql and request.question:
            if vanna_client.train_on_sql(request.question, request.sql):
                success_count += 1
                messages.append("成功添加 SQL 訓練資料")
            else:
                messages.append("添加 SQL 訓練資料失敗")
        elif request.sql or request.question:
            messages.append("SQL 訓練需要同時提供 question 和 sql 參數")
        
        if success_count == 0 and not messages:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="請至少提供一種訓練資料（ddl、documentation 或 sql+question）"
            )
        
        return TrainResponse(
            success=success_count > 0,
            message="; ".join(messages)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"訓練端點錯誤: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"訓練過程發生錯誤: {str(e)}"
        )


@router.get("/api/training-data")
async def get_training_data():
    """
    獲取當前的訓練資料
    
    返回已添加到 Vanna AI 模型中的所有訓練資料
    
    Returns:
        Dict: 訓練資料列表
    """
    try:
        if not vanna_client.is_initialized():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Vanna AI 服務尚未初始化，請稍後再試"
            )
        
        training_data = vanna_client.get_training_data()
        
        if training_data is None:
            return {"training_data": [], "count": 0}
        
        return {
            "training_data": training_data,
            "count": len(training_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取訓練資料錯誤: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取訓練資料時發生錯誤: {str(e)}"
        )

