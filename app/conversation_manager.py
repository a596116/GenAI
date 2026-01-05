"""
對話管理模塊
負責對話和消息的存儲與管理
"""

import json
import os
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ConversationManager:
    """對話管理器"""
    
    def __init__(self, storage_dir: str = "conversations_data"):
        """
        初始化對話管理器
        
        Args:
            storage_dir: 存儲目錄路徑
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        
        # 對話索引文件
        self.index_file = self.storage_dir / "conversations_index.json"
        
        # 加載或創建索引
        self._load_index()
    
    def _load_index(self):
        """加載對話索引"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    self.index = json.load(f)
            except Exception as e:
                logger.error(f"加載對話索引失敗: {e}")
                self.index = {"conversations": {}}
        else:
            self.index = {"conversations": {}}
            self._save_index()
    
    def _save_index(self):
        """保存對話索引"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存對話索引失敗: {e}")
    
    def _get_conversation_file(self, conversation_id: str) -> Path:
        """獲取對話文件路徑"""
        return self.storage_dir / f"{conversation_id}.json"
    
    def create_conversation(self, title: str = "新對話") -> Dict[str, Any]:
        """
        創建新對話
        
        Args:
            title: 對話標題
            
        Returns:
            Dict: 對話信息
        """
        conversation_id = f"conv_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()
        
        conversation = {
            "id": conversation_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
            "message_count": 0,
            "messages": []
        }
        
        # 保存對話文件
        conversation_file = self._get_conversation_file(conversation_id)
        try:
            with open(conversation_file, 'w', encoding='utf-8') as f:
                json.dump(conversation, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存對話文件失敗: {e}")
            raise
        
        # 更新索引
        self.index["conversations"][conversation_id] = {
            "id": conversation_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
            "message_count": 0
        }
        self._save_index()
        
        return {
            "conversation_id": conversation_id,
            "title": title,
            "created_at": now,
            "updated_at": now,
            "message_count": 0
        }
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        獲取對話詳情
        
        Args:
            conversation_id: 對話 ID
            
        Returns:
            Optional[Dict]: 對話信息，如果不存在則返回 None
        """
        conversation_file = self._get_conversation_file(conversation_id)
        
        if not conversation_file.exists():
            return None
        
        try:
            with open(conversation_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"讀取對話文件失敗: {e}")
            return None
    
    def list_conversations(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        獲取對話列表
        
        Args:
            limit: 返回數量限制
            offset: 偏移量
            
        Returns:
            List[Dict]: 對話列表
        """
        conversations = list(self.index["conversations"].values())
        
        # 按更新時間倒序排序
        conversations.sort(key=lambda x: x["updated_at"], reverse=True)
        
        # 分頁
        return conversations[offset:offset + limit]
    
    def update_conversation(self, conversation_id: str, title: Optional[str] = None) -> bool:
        """
        更新對話信息
        
        Args:
            conversation_id: 對話 ID
            title: 新標題
            
        Returns:
            bool: 是否成功
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return False
        
        now = datetime.now().isoformat()
        
        if title:
            conversation["title"] = title
        
        conversation["updated_at"] = now
        
        # 保存對話文件
        conversation_file = self._get_conversation_file(conversation_id)
        try:
            with open(conversation_file, 'w', encoding='utf-8') as f:
                json.dump(conversation, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"更新對話文件失敗: {e}")
            return False
        
        # 更新索引
        if conversation_id in self.index["conversations"]:
            if title:
                self.index["conversations"][conversation_id]["title"] = title
            self.index["conversations"][conversation_id]["updated_at"] = now
            self._save_index()
        
        return True
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        刪除對話
        
        Args:
            conversation_id: 對話 ID
            
        Returns:
            bool: 是否成功
        """
        conversation_file = self._get_conversation_file(conversation_id)
        
        # 刪除對話文件
        if conversation_file.exists():
            try:
                conversation_file.unlink()
            except Exception as e:
                logger.error(f"刪除對話文件失敗: {e}")
                return False
        
        # 從索引中移除
        if conversation_id in self.index["conversations"]:
            del self.index["conversations"][conversation_id]
            self._save_index()
        
        return True
    
    def add_message(self, conversation_id: str, role: str, content: str) -> Optional[Dict[str, Any]]:
        """
        添加消息到對話
        
        Args:
            conversation_id: 對話 ID
            role: 消息角色（user 或 assistant）
            content: 消息內容
            
        Returns:
            Optional[Dict]: 消息信息，如果失敗則返回 None
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return None
        
        message_id = f"msg_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()
        
        message = {
            "id": message_id,
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "created_at": now
        }
        
        # 添加消息
        conversation["messages"].append(message)
        conversation["message_count"] = len(conversation["messages"])
        conversation["updated_at"] = now
        
        # 如果是第一條用戶消息，更新對話標題
        if len(conversation["messages"]) == 1 and role == "user":
            conversation["title"] = content[:30] + ("..." if len(content) > 30 else "")
        
        # 保存對話文件
        conversation_file = self._get_conversation_file(conversation_id)
        try:
            with open(conversation_file, 'w', encoding='utf-8') as f:
                json.dump(conversation, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存消息失敗: {e}")
            return None
        
        # 更新索引
        if conversation_id in self.index["conversations"]:
            self.index["conversations"][conversation_id]["message_count"] = conversation["message_count"]
            self.index["conversations"][conversation_id]["updated_at"] = now
            if len(conversation["messages"]) == 1 and role == "user":
                self.index["conversations"][conversation_id]["title"] = conversation["title"]
            self._save_index()
        
        return message
    
    def get_messages(self, conversation_id: str, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        獲取對話的消息列表
        
        Args:
            conversation_id: 對話 ID
            limit: 返回數量限制
            offset: 偏移量
            
        Returns:
            List[Dict]: 消息列表
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return []
        
        messages = conversation.get("messages", [])
        return messages[offset:offset + limit]
    
    def clear_messages(self, conversation_id: str) -> bool:
        """
        清空對話的所有消息
        
        Args:
            conversation_id: 對話 ID
            
        Returns:
            bool: 是否成功
        """
        conversation = self.get_conversation(conversation_id)
        if not conversation:
            return False
        
        conversation["messages"] = []
        conversation["message_count"] = 0
        conversation["updated_at"] = datetime.now().isoformat()
        
        # 保存對話文件
        conversation_file = self._get_conversation_file(conversation_id)
        try:
            with open(conversation_file, 'w', encoding='utf-8') as f:
                json.dump(conversation, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"清空消息失敗: {e}")
            return False
        
        # 更新索引
        if conversation_id in self.index["conversations"]:
            self.index["conversations"][conversation_id]["message_count"] = 0
            self.index["conversations"][conversation_id]["updated_at"] = conversation["updated_at"]
            self._save_index()
        
        return True


# 創建全局實例
conversation_manager = ConversationManager()

