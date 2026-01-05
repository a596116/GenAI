"""
API 路由模塊
"""

from .chat import router as chat_router
from .training import router as training_router
from .database import router as database_router
from .conversations import router as conversations_router
from .health import router as health_router
from .root import router as root_router

__all__ = [
    "chat_router",
    "training_router",
    "database_router",
    "conversations_router",
    "health_router",
    "root_router"
]

