"""
Pydantic 資料模型
定義 API 請求和回應的資料結構
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ChatRequest(BaseModel):
    """聊天請求模型"""
    question: str = Field(..., description="用戶的自然語言問題", min_length=1)
    conversation_id: Optional[str] = Field(None, description="對話 ID（用於連續對話）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "顯示所有客戶的訂單總數",
                "conversation_id": "conv_123456"
            }
        }


class ChatResponse(BaseModel):
    """聊天回應模型"""
    question: str = Field(..., description="原始問題")
    sql: Optional[str] = Field(None, description="生成的 SQL 查詢")
    result: Optional[List[Dict[str, Any]]] = Field(None, description="查詢結果")
    explanation: Optional[str] = Field(None, description="查詢結果的解釋")
    error: Optional[str] = Field(None, description="錯誤訊息（如果有）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "顯示所有客戶的訂單總數",
                "sql": "SELECT customer_id, COUNT(*) as order_count FROM orders GROUP BY customer_id",
                "result": [
                    {"customer_id": 1, "order_count": 5},
                    {"customer_id": 2, "order_count": 3}
                ],
                "explanation": "查詢結果顯示每位客戶的訂單數量",
                "error": None
            }
        }


class TrainRequest(BaseModel):
    """訓練請求模型"""
    ddl: Optional[str] = Field(None, description="資料定義語言（DDL）語句")
    documentation: Optional[str] = Field(None, description="資料庫文檔或描述")
    sql: Optional[str] = Field(None, description="SQL 查詢範例")
    question: Optional[str] = Field(None, description="對應的自然語言問題（與 SQL 配對）")
    
    class Config:
        json_schema_extra = {
            "example": {
                "ddl": "CREATE TABLE customers (id INT PRIMARY KEY, name VARCHAR(100))",
                "documentation": "customers 表儲存所有客戶資訊",
                "sql": "SELECT * FROM customers WHERE id = 1",
                "question": "顯示 ID 為 1 的客戶"
            }
        }


class TrainResponse(BaseModel):
    """訓練回應模型"""
    success: bool = Field(..., description="訓練是否成功")
    message: str = Field(..., description="訓練結果訊息")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "成功添加訓練資料到 Vanna AI 模型"
            }
        }


class HealthResponse(BaseModel):
    """健康檢查回應模型"""
    status: str = Field(..., description="服務狀態")
    database_connected: bool = Field(..., description="資料庫連接狀態")
    vanna_initialized: bool = Field(..., description="Vanna AI 初始化狀態")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "database_connected": True,
                "vanna_initialized": True
            }
        }


class TableInfo(BaseModel):
    """資料表資訊模型"""
    table_name: str = Field(..., description="表名稱")
    table_schema: Optional[str] = Field(None, description="表結構描述")
    
    class Config:
        json_schema_extra = {
            "example": {
                "table_name": "customers",
                "table_schema": "CREATE TABLE customers (id INT, name VARCHAR(100))"
            }
        }


class TablesResponse(BaseModel):
    """資料表列表回應模型"""
    tables: List[TableInfo] = Field(..., description="資料表列表")
    count: int = Field(..., description="資料表總數")
    
    class Config:
        json_schema_extra = {
            "example": {
                "tables": [
                    {"table_name": "customers", "table_schema": "CREATE TABLE customers (...)"},
                    {"table_name": "orders", "table_schema": "CREATE TABLE orders (...)"}
                ],
                "count": 2
            }
        }


# ===== 對話管理相關模型 =====

class ConversationCreate(BaseModel):
    """創建對話請求模型"""
    title: Optional[str] = Field("新對話", description="對話標題")
    
    class Config:
        json_schema_extra = {
            "example": {
                "title": "數據查詢對話"
            }
        }


class ConversationResponse(BaseModel):
    """對話回應模型"""
    conversation_id: str = Field(..., description="對話 ID")
    title: str = Field(..., description="對話標題")
    created_at: str = Field(..., description="創建時間")
    updated_at: str = Field(..., description="更新時間")
    message_count: int = Field(0, description="消息數量")
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversation_id": "conv_123456",
                "title": "數據查詢對話",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-01T01:00:00",
                "message_count": 5
            }
        }


class ConversationListResponse(BaseModel):
    """對話列表回應模型"""
    conversations: List[ConversationResponse] = Field(..., description="對話列表")
    count: int = Field(..., description="對話總數")
    
    class Config:
        json_schema_extra = {
            "example": {
                "conversations": [
                    {
                        "conversation_id": "conv_123456",
                        "title": "數據查詢對話",
                        "created_at": "2024-01-01T00:00:00",
                        "updated_at": "2024-01-01T01:00:00",
                        "message_count": 5
                    }
                ],
                "count": 1
            }
        }


class MessageCreate(BaseModel):
    """創建消息請求模型"""
    role: str = Field(..., description="消息角色（user 或 assistant）")
    content: str = Field(..., description="消息內容")
    
    class Config:
        json_schema_extra = {
            "example": {
                "role": "user",
                "content": "顯示所有用戶資料"
            }
        }


class MessageResponse(BaseModel):
    """消息回應模型"""
    message_id: str = Field(..., description="消息 ID")
    conversation_id: str = Field(..., description="對話 ID")
    role: str = Field(..., description="消息角色")
    content: str = Field(..., description="消息內容")
    created_at: str = Field(..., description="創建時間")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "msg_123456",
                "conversation_id": "conv_123456",
                "role": "user",
                "content": "顯示所有用戶資料",
                "created_at": "2024-01-01T00:00:00"
            }
        }


class MessageListResponse(BaseModel):
    """消息列表回應模型"""
    messages: List[MessageResponse] = Field(..., description="消息列表")
    count: int = Field(..., description="消息總數")
    
    class Config:
        json_schema_extra = {
            "example": {
                "messages": [
                    {
                        "message_id": "msg_123456",
                        "conversation_id": "conv_123456",
                        "role": "user",
                        "content": "顯示所有用戶資料",
                        "created_at": "2024-01-01T00:00:00"
                    }
                ],
                "count": 1
            }
        }


# ===== 外部數據庫連接相關模型 =====

class DatabaseConnectionRequest(BaseModel):
    """數據庫連接請求模型"""
    connection_string: str = Field(..., description="數據庫連接字符串，格式：mysql://user:password@host:port/database")
    
    class Config:
        json_schema_extra = {
            "example": {
                "connection_string": "mysql://user:password@localhost:3306/database_name"
            }
        }


class QuestionSuggestion(BaseModel):
    """問題建議模型"""
    question: str = Field(..., description="建議的問題")
    description: Optional[str] = Field(None, description="問題描述")
    
    class Config:
        json_schema_extra = {
            "example": {
                "question": "顯示所有用戶資料",
                "description": "查詢所有用戶的信息"
            }
        }


class DatabaseQuestionsResponse(BaseModel):
    """數據庫問題建議回應模型"""
    suggestions: List[QuestionSuggestion] = Field(..., description="問題建議列表")
    count: int = Field(..., description="建議問題總數")
    database_name: str = Field(..., description="數據庫名稱")
    table_count: int = Field(..., description="表數量")
    
    class Config:
        json_schema_extra = {
            "example": {
                "suggestions": [
                    {"question": "顯示所有用戶資料", "description": "查詢所有用戶的信息"},
                    {"question": "統計每個部門的員工數量", "description": "按部門分組統計員工數量"}
                ],
                "count": 2,
                "database_name": "my_database",
                "table_count": 5
            }
        }

