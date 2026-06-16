"""小组赛与排名 API。"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.deps import get_session
from app.services.match_service import (
    get_group_matches as svc_get_group_matches,
    serialize_match,
)
from app.services.odds_service import get_odds_sources  # noqa: F401 保留兼容
from app.services.ranking_service import get_group_rankings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["groups"])


def _build_sporttery_live_odds_map() -> dict:
    """尝试从体彩拉取实时赔率（合并到小组赛显示）。失败返回空。"""
    try:
        from app.services.sporttery_provider import SportteryProvider
        provider = SportteryProvider('sporttery', {'page_size': 100})
        live_matches = provider.fetch_all_play_types()
        live_map = {}
        for lm in live_matches:
            if lm.get('had'):
                key = (lm.get('home_team', ''), lm.get('away_team', ''))
                live_map[key] = lm.get('had')
        return live_map
    except Exception:
        return {}


@router.get("/group_stage")
def api_group_stage(
    group: Optional[str] = None,
    session: Session = Depends(get_session),
):
    """获取小组赛比赛。支持 ?group=X 查询参数。"""
    try:
        raw = svc_get_group_matches(session, group)
        matches = [serialize_match(m, o) for m, o in raw]

        live_map = _build_sporttery_live_odds_map()
        for m in matches:
            key = (m.get('team1', ''), m.get('team2', ''))
            if key in live_map:
                had = live_map[key]
                m['odds'] = {
                    'win_odds': had.get('win'),
                    'draw_odds': had.get('draw'),
                    'lose_odds': had.get('lose'),
                    'update_time': had.get('update_time'),
                    'source': 'sporttery',
                }

        return {
            'matches': matches,
            'current_group': group or '',
        }
    except Exception as e:
        logger.exception("api_group_stage 失败")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rankings")
def api_rankings(
    group: Optional[str] = None,
    session: Session = Depends(get_session),
):
    """获取小组排名。支持 ?group=X 查询参数。"""
    try:
        rankings = get_group_rankings(session, group)
        return {
            'rankings': rankings,
            'current_group': group or '',
        }
    except Exception as e:
        logger.exception("api_rankings 失败")
        raise HTTPException(status_code=500, detail=str(e))
