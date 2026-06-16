"""国旗 API。"""
from fastapi import APIRouter

from app.utils.flags import get_flag_map_dict

router = APIRouter(prefix="/api/v1", tags=["flags"])


@router.get("/flags")
def api_flags():
    """返回国旗映射字典（供前端使用）。"""
    return get_flag_map_dict()
