"""比赛相关 API。"""
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.deps import get_session
from app.services.match_service import (
    get_matches_by_date as svc_get_matches_by_date,
    get_upcoming_matches,
    group_matches_by_date,
    serialize_match,
    update_match_result,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["matches"])


class UpdateResultPayload(BaseModel):
    score1: int
    score2: int


@router.get("/matches")
def api_matches(
    date: Optional[str] = None,
    session: Session = Depends(get_session),
):
    """获取比赛列表。支持 ?date=YYYY-MM-DD 查询参数。"""
    try:
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        day_raw = svc_get_matches_by_date(session, date)
        day_matches = [serialize_match(m, o) for m, o in day_raw]

        tomorrow = (
            datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)
        ).strftime("%Y-%m-%d")
        upcoming_raw = get_upcoming_matches(session, tomorrow, 7)
        upcoming_matches = [serialize_match(m, o) for m, o in upcoming_raw]

        grouped_raw = group_matches_by_date(upcoming_raw)
        grouped_upcoming = {
            d: [serialize_match(m, o) for m, o in items]
            for d, items in grouped_raw.items()
        }

        return {
            'day_matches': day_matches,
            'upcoming_matches': upcoming_matches,
            'grouped_upcoming': grouped_upcoming,
        }
    except Exception as e:
        logger.exception("api_matches 失败")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/matches/{match_id}/result")
def api_update_result(
    match_id: int,
    payload: UpdateResultPayload,
    session: Session = Depends(get_session),
):
    """更新比赛结果。"""
    try:
        update_match_result(session, match_id, payload.score1, payload.score2)
        return {'status': 'success', 'message': '比赛结果已更新'}
    except Exception as e:
        logger.exception("api_update_result 失败")
        raise HTTPException(status_code=500, detail=str(e))
