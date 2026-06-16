"""
赔率抓取服务 - 支持多数据源配置
"""
import logging
import requests
import json
import time
import random
from abc import abstractmethod
from datetime import datetime
from typing import List, Dict, Optional, Tuple
import backend.db
from backend.services.odds_base import OddsData, OddsProvider

logger = logging.getLogger(__name__)


class MockOddsProvider(OddsProvider):
    """模拟数据源（用于测试）"""
    
    def fetch_odds(self) -> List[OddsData]:
        """返回模拟数据"""
        logger.info(f"[{self.name}] 使用模拟数据")
        mock_data = [
            {"team1": "巴西", "team2": "阿根廷", "win_odds": 1.85, "draw_odds": 3.40, "lose_odds": 4.20},
            {"team1": "法国", "team2": "德国", "win_odds": 2.10, "draw_odds": 3.25, "lose_odds": 3.60},
            {"team1": "英格兰", "team2": "西班牙", "win_odds": 2.35, "draw_odds": 3.15, "lose_odds": 3.10},
            {"team1": "葡萄牙", "team2": "荷兰", "win_odds": 2.05, "draw_odds": 3.30, "lose_odds": 3.70},
            {"team1": "比利时", "team2": "意大利", "win_odds": 2.25, "draw_odds": 3.20, "lose_odds": 3.30},
        ]
        
        result = []
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for item in mock_data:
            result.append(OddsData(
                team1=item["team1"],
                team2=item["team2"],
                win_odds=item["win_odds"],
                draw_odds=item["draw_odds"],
                lose_odds=item["lose_odds"],
                source=self.name,
                updated_at=now
            ))
        return result


class ApiFootballProvider(OddsProvider):
    """
    API-Football 数据源
    官网: https://www.api-football.com/
    需要注册获取 API Key
    """
    
    def fetch_odds(self) -> List[OddsData]:
        """从 API-Football 获取赔率"""
        api_key = self.config.get('api_key')
        if not api_key:
            logger.warning(f"[{self.name}] 未配置 API Key")
            return []
        
        base_url = "https://v3.football.api-sports.io/odds"
        headers = {
            'x-rapidapi-key': api_key,
            'x-rapidapi-host': 'v3.football.api-sports.io'
        }
        
        try:
            # 2026世界杯联赛ID (需要确认实际ID)
            league_id = self.config.get('league_id', '1')  # 默认为世界杯
            season = self.config.get('season', '2026')
            
            response = requests.get(
                f"{base_url}?league={league_id}&season={season}",
                headers=headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            return self._parse_response(data)
            
        except Exception as e:
            logger.error(f"[{self.name}] 获取赔率失败: {e}")
            return []
    
    def _parse_response(self, data: dict) -> List[OddsData]:
        """解析 API-Football 响应"""
        result = []
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        for fixture in data.get('response', []):
            try:
                match_info = fixture.get('fixture', {})
                teams = fixture.get('teams', {})
                odds = fixture.get('odds', [])
                
                if not odds:
                    continue
                
                # 获取 1x2 赔率
                bookmaker = odds[0].get('bookmakers', [{}])[0]
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
                        team1=team1,
                        team2=team2,
                        win_odds=float(home_odd.get('odd', 0)),
                        draw_odds=float(draw_odd.get('odd', 0)),
                        lose_odds=float(away_odd.get('odd', 0)),
                        source=self.name,
                        updated_at=now
                    ))
                    
            except Exception as e:
                logger.warning(f"[{self.name}] 解析比赛数据失败: {e}")
                continue
        
        logger.info(f"[{self.name}] 成功获取 {len(result)} 条赔率")
        return result


class WebScraperProvider(OddsProvider):
    """
    网页抓取数据源基类
    子类需要实现 parse_html 方法
    """
    
    def fetch_odds(self) -> List[OddsData]:
        """抓取网页并解析"""
        url = self.config.get('url')
        if not url:
            logger.warning(f"[{self.name}] 未配置 URL")
            return []
        
        try:
            # 随机延迟避免反爬
            delay = self.config.get('delay', (1, 3))
            time.sleep(random.uniform(*delay))
            
            headers = self._get_headers()
            headers.update(self.config.get('extra_headers', {}))
            
            response = requests.get(
                url,
                headers=headers,
                timeout=self.config.get('timeout', 30),
                proxies=self.config.get('proxies')
            )
            response.raise_for_status()
            
            return self.parse_html(response.text)
            
        except Exception as e:
            logger.error(f"[{self.name}] 抓取失败: {e}")
            return []
    
    @abstractmethod
    def parse_html(self, html: str) -> List[OddsData]:
        """子类实现具体的 HTML 解析逻辑"""
        pass


class OddsCrawlerManager:
    """赔率抓取管理器"""
    
    # 默认配置
    DEFAULT_PROVIDERS = {
        'mock': {
            'enabled': True,
            'priority': 99,  # 最低优先级，作为后备
            'class': 'MockOddsProvider'
        }
    }
    
    def __init__(self, config: Optional[dict] = None):
        self.config = config or self.DEFAULT_PROVIDERS
        self.providers: List[OddsProvider] = []
        self._init_providers()
    
    def _init_providers(self):
        """初始化所有启用的数据源"""
        # 延迟导入避免循环依赖
        from backend.services.sporttery_provider import SportteryProvider

        provider_classes = {
            'MockOddsProvider': MockOddsProvider,
            'ApiFootballProvider': ApiFootballProvider,
            'WebScraperProvider': WebScraperProvider,
            'SportteryProvider': SportteryProvider,
        }
        
        # 按优先级排序
        sorted_configs = sorted(
            self.config.items(),
            key=lambda x: x[1].get('priority', 1)
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
        """
        从所有数据源抓取赔率，按优先级合并
        高优先级数据源的赔率会覆盖低优先级的
        """
        all_odds: Dict[Tuple[str, str], OddsData] = {}
        
        for provider in self.providers:
            try:
                odds_list = provider.fetch_odds()
                for odds in odds_list:
                    key = (odds.team1, odds.team2)
                    # 优先级高的覆盖优先级低的
                    if key not in all_odds:
                        all_odds[key] = odds
                        logger.debug(f"添加赔率: {odds.team1} vs {odds.team2} @ {odds.source}")
            except Exception as e:
                logger.error(f"从 {provider.name} 获取赔率失败: {e}")
                continue
        
        return list(all_odds.values())
    
    def update_database(self) -> Tuple[int, int]:
        """
        更新数据库中的赔率
        返回: (成功更新的比赛数, 跳过的比赛数)
        """
        odds_list = self.fetch_all_odds()
        
        if not odds_list:
            logger.warning("没有获取到任何赔率数据")
            return 0, 0
        
        conn = backend.db.db_pool.get_connection()
        try:
            cursor = conn.cursor()
            
            # 获取所有未结束的比赛
            cursor.execute(
                "SELECT id, team1, team2 FROM matches WHERE status = 'upcoming'"
            )
            matches = cursor.fetchall()
            
            updated = 0
            skipped = 0
            
            for match_id, team1, team2 in matches:
                # 查找匹配的赔率
                matching_odds = None
                for odds in odds_list:
                    # 支持模糊匹配
                    if self._match_teams(team1, team2, odds.team1, odds.team2):
                        matching_odds = odds
                        break
                
                if matching_odds:
                    # 先检查是否已有相同赔率记录（避免重复插入）
                    cursor.execute(
                        """SELECT COUNT(*) FROM odds 
                           WHERE match_id = ? 
                           AND win_odds = ? 
                           AND draw_odds = ? 
                           AND lose_odds = ?""",
                        (match_id, 
                         matching_odds.win_odds, 
                         matching_odds.draw_odds, 
                         matching_odds.lose_odds)
                    )
                    existing_count = cursor.fetchone()[0]
                    
                    if existing_count > 0:
                        # 已有相同赔率记录，跳过
                        skipped += 1
                        continue
                    
                    # 没有相同赔率记录，插入新记录
                    cursor.execute(
                        """INSERT INTO odds 
                           (match_id, win_odds, draw_odds, lose_odds, update_time, source) 
                           VALUES (?, ?, ?, ?, ?, ?)""",
                        (match_id, 
                         matching_odds.win_odds, 
                         matching_odds.draw_odds, 
                         matching_odds.lose_odds,
                         matching_odds.updated_at,
                         matching_odds.source)
                    )
                    updated += 1
                    logger.debug(f"更新赔率: {team1} vs {team2}")
                else:
                    skipped += 1
            
            conn.commit()
            logger.info(f"赔率更新完成: 成功 {updated} 场, 跳过 {skipped} 场")
            return updated, skipped
            
        except Exception as e:
            logger.error(f"更新数据库失败: {e}")
            conn.rollback()
            return 0, 0
        finally:
            backend.db.db_pool.return_connection(conn)
    
    def _match_teams(self, db_team1: str, db_team2: str, 
                     odds_team1: str, odds_team2: str) -> bool:
        """检查队伍名称是否匹配（支持模糊匹配）"""
        # 精确匹配
        if db_team1 == odds_team1 and db_team2 == odds_team2:
            return True
        
        # 标准化后匹配
        from backend.utils.normalize import normalize_team_name
        n_db1 = normalize_team_name(db_team1)
        n_db2 = normalize_team_name(db_team2)
        n_odds1 = normalize_team_name(odds_team1)
        n_odds2 = normalize_team_name(odds_team2)
        
        return n_db1 == n_odds1 and n_db2 == n_odds2


# 全局爬虫管理器实例
crawler_manager: Optional[OddsCrawlerManager] = None


def init_crawler_manager(config: Optional[dict] = None):
    """初始化全局爬虫管理器"""
    global crawler_manager
    crawler_manager = OddsCrawlerManager(config)
    return crawler_manager


def update_odds() -> Tuple[int, int]:
    """更新赔率的便捷函数"""
    global crawler_manager
    if crawler_manager is None:
        crawler_manager = OddsCrawlerManager()
    return crawler_manager.update_database()


def get_odds_sources() -> List[Dict]:
    """获取所有数据源状态"""
    global crawler_manager
    if crawler_manager is None:
        return []
    
    return [
        {
            'name': p.name,
            'enabled': p.enabled,
            'priority': p.priority,
            'type': p.__class__.__name__
        }
        for p in crawler_manager.providers
    ]
