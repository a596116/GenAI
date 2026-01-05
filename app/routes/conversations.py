"""
對話管理路由
"""

import logging
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, status
from app.models import (
    ConversationCreate,
    ConversationResponse,
    ConversationListResponse,
    MessageCreate,
    MessageResponse,
    MessageListResponse
)
from app.conversation_manager import conversation_manager

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Conversations"])


@router.post("/api/conversations", response_model=ConversationResponse)
async def create_conversation(request: ConversationCreate):
    """
    創建新對話
    
    Args:
        request: 創建對話請求
        
    Returns:
        ConversationResponse: 新創建的對話信息
    """
    try:
        conversation = conversation_manager.create_conversation(request.title or "新對話")
        return ConversationResponse(**conversation)
    except Exception as e:
        logger.error(f"創建對話錯誤: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"創建對話時發生錯誤: {str(e)}"
        )


@router.get("/api/conversations", response_model=ConversationListResponse)
async def list_conversations(limit: int = 100, offset: int = 0):
    """
    獲取對話列表
    
    Args:
        limit: 返回數量限制
        offset: 偏移量
        
    Returns:
        ConversationListResponse: 對話列表
    """
    try:
        conversations = conversation_manager.list_conversations(limit, offset)
        # 將 "id" 字段轉換為 "conversation_id" 以匹配 ConversationResponse 模型
        formatted_conversations = []
        for conv in conversations:
            conv_dict = conv.copy()
            # 如果存在 "id" 字段，重命名為 "conversation_id"
            if "id" in conv_dict and "conversation_id" not in conv_dict:
                conv_dict["conversation_id"] = conv_dict.pop("id")
            formatted_conversations.append(conv_dict)
        
        return ConversationListResponse(
            conversations=[ConversationResponse(**conv) for conv in formatted_conversations],
            count=len(formatted_conversations)
        )
    except Exception as e:
        logger.error(f"獲取對話列表錯誤: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取對話列表時發生錯誤: {str(e)}"
        )


@router.get("/api/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: str):
    """
    獲取對話詳情
    
    Args:
        conversation_id: 對話 ID
        
    Returns:
        ConversationResponse: 對話信息
    """
    try:
        conversation = conversation_manager.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"對話 {conversation_id} 不存在"
            )
        
        return ConversationResponse(
            conversation_id=conversation["id"],
            title=conversation["title"],
            created_at=conversation["created_at"],
            updated_at=conversation["updated_at"],
            message_count=conversation["message_count"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取對話詳情錯誤: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取對話詳情時發生錯誤: {str(e)}"
        )


@router.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """
    刪除對話
    
    Args:
        conversation_id: 對話 ID
        
    Returns:
        Dict: 刪除結果
    """
    try:
        success = conversation_manager.delete_conversation(conversation_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"對話 {conversation_id} 不存在"
            )
        
        return {"success": True, "message": "對話已刪除"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"刪除對話錯誤: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"刪除對話時發生錯誤: {str(e)}"
        )


@router.post("/api/conversations/{conversation_id}/messages", response_model=MessageResponse)
async def add_message(conversation_id: str, request: MessageCreate):
    """
    添加消息到對話
    
    Args:
        conversation_id: 對話 ID
        request: 消息內容
        
    Returns:
        MessageResponse: 新添加的消息信息
    """
    try:
        message = conversation_manager.add_message(
            conversation_id,
            request.role,
            request.content
        )
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"對話 {conversation_id} 不存在"
            )
        
        return MessageResponse(
            message_id=message["id"],
            conversation_id=message["conversation_id"],
            role=message["role"],
            content=message["content"],
            created_at=message["created_at"]
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"添加消息錯誤: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"添加消息時發生錯誤: {str(e)}"
        )


@router.get("/api/conversations/{conversation_id}/messages", response_model=MessageListResponse)
async def get_messages(conversation_id: str, limit: int = 100, offset: int = 0):
    """
    獲取對話的消息列表
    
    Args:
        conversation_id: 對話 ID
        limit: 返回數量限制
        offset: 偏移量
        
    Returns:
        MessageListResponse: 消息列表
    """
    try:
        logger.info(f"獲取對話消息: conversation_id={conversation_id}, limit={limit}, offset={offset}")
        messages = conversation_manager.get_messages(conversation_id, limit, offset)
        
        if not messages:
            logger.info(f"對話 {conversation_id} 沒有消息")
            return MessageListResponse(messages=[], count=0)
        
        logger.info(f"找到 {len(messages)} 條消息")
        
        # 轉換消息格式
        message_responses = []
        for msg in messages:
            try:
                message_responses.append(
                    MessageResponse(
                        message_id=msg.get("id", f"msg_{uuid.uuid4().hex[:12]}"),
                        conversation_id=msg.get("conversation_id", conversation_id),
                        role=msg.get("role", "user"),
                        content=msg.get("content", ""),
                        created_at=msg.get("created_at", datetime.now().isoformat())
                    )
                )
            except Exception as e:
                logger.warning(f"轉換消息格式時出錯: {e}, 消息: {msg}")
                continue
        
        return MessageListResponse(
            messages=message_responses,
            count=len(message_responses)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"獲取消息列表錯誤: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"獲取消息列表時發生錯誤: {str(e)}"
        )


@router.delete("/api/conversations/{conversation_id}/messages")
async def clear_messages(conversation_id: str):
    """
    清空對話的所有消息
    
    Args:
        conversation_id: 對話 ID
        
    Returns:
        Dict: 清空結果
    """
    try:
        success = conversation_manager.clear_messages(conversation_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"對話 {conversation_id} 不存在"
            )
        
        return {"success": True, "message": "消息已清空"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"清空消息錯誤: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"清空消息時發生錯誤: {str(e)}"
        )

