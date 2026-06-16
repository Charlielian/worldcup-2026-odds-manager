"""淘汰赛 API。"""
import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.deps import get_session
from app.services.knockout_service import get_knockout_bracket_data
from app.services.match_service import (
    get_knockout_matches as svc_get_knockout_matches,
    serialize_match,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["knockout"])


def _build_sporttery_live_odds_map() -> dict:
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


@router.get("/knockout")
def api_knockout(session: Session = Depends(get_session)):
    """获取淘汰赛比赛列表。"""
    try:
        raw = svc_get_knockout_matches(session)
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
        return {'matches': matches}
    except Exception as e:
        logger.exception("api_knockout 失败")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knockout/bracket")
def api_knockout_bracket(session: Session = Depends(get_session)):
    """获取淘汰赛对阵图数据。"""
    try:
        bracket_data = get_knockout_bracket_data(session)
        return {'bracket_data': bracket_data}
    except Exception as e:
        logger.exception("api_knockout_bracket 失败")
        raise HTTPException(status_code=500, detail=str(e))
