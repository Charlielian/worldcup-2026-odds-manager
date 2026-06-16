"""通用依赖：DB Session、Settings。"""
from app.database import get_session
from app.config import Settings, get_settings

__all__ = ["get_session", "get_settings", "Settings"]
