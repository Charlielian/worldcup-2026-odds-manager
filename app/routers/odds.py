"""赔率管理 API。"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.deps import get_session
from app.security import admin_required
from app.services.odds_service import (
    crawler_manager,
    get_odds_sources,
    update_odds_sync,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["odds"])


@router.get("/odds/sources")
def api_odds_sources():
    """返回赔率数据源列表和状态。"""
    return {'sources': get_odds_sources()}


@router.post("/odds/update")
def api_odds_update(
    _token: str = Depends(admin_required),
    session: Session = Depends(get_session),
):
    """手动触发赔率更新（管理用）。"""
    try:
        updated, skipped = update_odds_sync(session)
        return {
            'status': 'success',
            'message': f'赔率更新完成: 成功 {updated} 场, 跳过 {skipped} 场',
            'updated': updated,
            'skipped': skipped,
        }
    except Exception as e:
        logger.exception("手动更新赔率失败")
        raise HTTPException(status_code=500, detail=str(e))
