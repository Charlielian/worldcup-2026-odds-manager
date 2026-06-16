"""体彩实时赔率 API。"""
import logging
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["live"])


@router.get("/live/matches")
def api_live_matches():
    """获取体彩当前在售比赛及全部玩法赔率（实时数据）。"""
    try:
        from app.services.sporttery_provider import SportteryProvider
        provider = SportteryProvider('sporttery', {
            'pool_code': 'had,hhad,crs,ttg,bqc',
            'page_size': 100,
            'page_delay': 0.5,
            'timeout': 30,
        })
        all_matches = provider.fetch_all_play_types()
        matches_by_date = {}
        for m in all_matches:
            d = m.get('match_date', '未知日期')
            matches_by_date.setdefault(d, []).append(m)
        return {
            'total': len(all_matches),
            'matches_by_date': matches_by_date,
            'all_matches': all_matches,
        }
    except Exception as e:
        logger.exception("获取体彩实时数据失败")
        raise HTTPException(status_code=500, detail=str(e))
