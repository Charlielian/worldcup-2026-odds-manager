"""赔率抓取与多数据源管理。"""
import logging
import random
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import requests
from sqlmodel import Session, select

from app.models.match import Match, Odds
from app.services.odds_base import OddsData, OddsProvider
from app.services.sporttery_provider import SportteryProvider
from app.utils.normalize import normalize_team_name

logger = logging.getLogger(__name__)


class MockOddsProvider(OddsProvider):
    """模拟数据源（用于测试）。"""

    def fetch_odds(self) -> List[OddsData]:
        logger.info(f"[{self.name}] 使用模拟数据")
        mock = [
            {"team1": "巴西", "team2": "阿根廷", "win_odds": 1.85, "draw_odds": 3.40, "lose_odds": 4.20},
            {"team1": "法国", "team2": "德国", "win_odds": 2.10, "draw_odds": 3.25, "lose_odds": 3.60},
            {"team1": "英格兰", "team2": "西班牙", "win_odds": 2.35, "draw_odds": 3.15, "lose_odds": 3.10},
            {"team1": "葡萄牙", "team2": "荷兰", "win_odds": 2.05, "draw_odds": 3.30, "lose_odds": 3.70},
            {"team1": "比利时", "team2": "意大利", "win_odds": 2.25, "draw_odds": 3.20, "lose_odds": 3.30},
        ]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return [
            OddsData(
                team1=item["team1"], team2=item["team2"],
                win_odds=item["win_odds"], draw_odds=item["draw_odds"], lose_odds=item["lose_odds"],
                source=self.name, updated_at=now,
            )
            for item in mock
        ]


class ApiFootballProvider(OddsProvider):
    """API-Football 数据源。"""

    def fetch_odds(self) -> List[OddsData]:
        api_key = self.config.get('api_key')
        if not api_key:
            logger.warning(f"[{self.name}] 未配置 API Key")
            return []

        base_url = "https://v3.football.api-sports.io/odds"
        headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': 'v3.football.api-sports.io',
        }
        try:
            league_id = self.config.get('league_id', '1')
            season = self.config.get('season', '2026')
            response = requests.get(
                f"{base_url}?league={league_id}&season={season}",
                headers=headers, timeout=30,
            )
            response.raise_for_status()
            return self._parse_response(response.json())
        except Exception as e:
            logger.error(f"[{self.name}] 获取赔率失败: {e}")
            return []

    def _parse_response(self, data: dict) -> List[OddsData]:
        result = []
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for fixture in data.get('response', []):
            try:
                teams = fixture.get('teams', {})
                odds_list = fixture.get('odds', [])
                if not odds_list:
                    continue
                bookmaker = odds_list[0].get('bookmakers', [{}])[0]
                bets = bookmaker.get('bets', [])
                match_winner = next((b for b in bets if b.get('name') == 'Match Winner'), None)
                if not match_winner:
                    continue
                values = match_winner.get('values', [])
                home_odd = next((v for v in values if v.get('value') == 'Home'), {})
                draw_odd = next((v for v in values if v.get('value') == 'Draw'), {})
                away_odd = next((v for v in values if v.get('value') == 'Away'), {})
                team1 = teams.get('home', {}).get('name', '')
                team2 = teams.get('away', {}).get('name', '')
                if team1 and team2:
                    result.append(OddsData(
                        team1=team1, team2=team2,
                        win_odds=float(home_odd.get('odd', 0)),
                        draw_odds=float(draw_odd.get('odd', 0)),
                        lose_odds=float(away_odd.get('odd', 0)),
                        source=self.name, updated_at=now,
                    ))
            except Exception as e:
                logger.warning(f"[{self.name}] 解析比赛数据失败: {e}")
                continue
        logger.info(f"[{self.name}] 成功获取 {len(result)} 条赔率")
        return result


class OddsCrawlerManager:
    """赔率抓取管理器。"""

    DEFAULT_PROVIDERS = {
        'mock': {
            'enabled': True,
            'priority': 99,
            'class': 'MockOddsProvider',
        }
    }

    def __init__(self, config: Optional[dict] = None):
        self.config = config or self.DEFAULT_PROVIDERS
        self.providers: List[OddsProvider] = []
        self._init_providers()

    def _init_providers(self):
        provider_classes = {
            'MockOddsProvider': MockOddsProvider,
            'ApiFootballProvider': ApiFootballProvider,
            'SportteryProvider': SportteryProvider,
        }
        sorted_configs = sorted(
            self.config.items(),
            key=lambda x: x[1].get('priority', 1),
        )
        for name, cfg in sorted_configs:
            if not cfg.get('enabled', True):
                continue
            class_name = cfg.get('class', 'MockOddsProvider')
            provider_class = provider_classes.get(class_name)
            if provider_class:
                try:
                    provider = provider_class(name, cfg)
                    self.providers.append(provider)
                    logger.info(f"初始化数据源: {name} (优先级: {cfg.get('priority', 1)})")
                except Exception as e:
                    logger.error(f"初始化数据源 {name} 失败: {e}")
            else:
                logger.warning(f"未知的数据源类型: {class_name}")

    def fetch_all_odds(self) -> List[OddsData]:
        all_odds: Dict[Tuple[str, str], OddsData] = {}
        for provider in self.providers:
            try:
                odds_list = provider.fetch_odds()
                for odds in odds_list:
                    key = (odds.team1, odds.team2)
                    if key not in all_odds:
                        all_odds[key] = odds
            except Exception as e:
                logger.error(f"从 {provider.name} 获取赔率失败: {e}")
                continue
        return list(all_odds.values())

    def update_database(self, session: Session) -> Tuple[int, int]:
        odds_list = self.fetch_all_odds()
        if not odds_list:
            logger.warning("没有获取到任何赔率数据")
            return 0, 0

        matches = list(session.exec(
            select(Match.id, Match.team1, Match.team2)
            .where(Match.status == 'upcoming')
        ).all())

        updated = 0
        skipped = 0
        for match_id, team1, team2 in matches:
            matching_odds = None
            for odds in odds_list:
                if self._match_teams(team1, team2, odds.team1, odds.team2):
                    matching_odds = odds
                    break
            if matching_odds:
                session.add(Odds(
                    match_id=match_id,
                    win_odds=matching_odds.win_odds,
                    draw_odds=matching_odds.draw_odds,
                    lose_odds=matching_odds.lose_odds,
                    update_time=matching_odds.updated_at,
                    source=matching_odds.source,
                ))
                updated += 1
            else:
                skipped += 1
        session.commit()
        logger.info(f"赔率更新完成: 成功 {updated} 场, 跳过 {skipped} 场")
        return updated, skipped

    @staticmethod
    def _match_teams(db_team1: str, db_team2: str,
                     odds_team1: str, odds_team2: str) -> bool:
        if db_team1 == odds_team1 and db_team2 == odds_team2:
            return True
        return (
            normalize_team_name(db_team1) == normalize_team_name(odds_team1)
            and normalize_team_name(db_team2) == normalize_team_name(odds_team2)
        )


# 全局爬虫管理器
crawler_manager: Optional[OddsCrawlerManager] = None


def init_crawler_manager(config: Optional[dict] = None) -> OddsCrawlerManager:
    global crawler_manager
    crawler_manager = OddsCrawlerManager(config)
    return crawler_manager


def get_odds_sources() -> List[dict]:
    if crawler_manager is None:
        return []
    return [
        {
            'name': p.name,
            'enabled': p.enabled,
            'priority': p.priority,
            'type': p.__class__.__name__,
        }
        for p in crawler_manager.providers
    ]


def update_odds_sync(session: Session) -> Tuple[int, int]:
    """同步执行一次赔率更新（线程内调用）。"""
    global crawler_manager
    if crawler_manager is None:
        from app.config import get_settings
        settings = get_settings()
        crawler_manager = OddsCrawlerManager(settings.ODDS_PROVIDERS.get('providers', {}))
    return crawler_manager.update_database(session)
