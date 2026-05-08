"""
赔率数据源抽象基类和数据结构
"""
import logging
from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class OddsData:
    """赔率数据结构"""
    team1: str
    team2: str
    win_odds: float   # 主队胜赔率
    draw_odds: float  # 平局赔率
    lose_odds: float  # 客队胜赔率
    source: str       # 数据来源
    updated_at: str   # 数据更新时间


class OddsProvider(ABC):
    """赔率数据源抽象基类"""

    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config
        self.enabled = config.get('enabled', True)
        self.priority = config.get('priority', 1)

    @abstractmethod
    def fetch_odds(self) -> List[OddsData]:
        """抓取赔率数据，返回 OddsData 列表"""
        pass

    def _get_headers(self) -> dict:
        """获取默认请求头"""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0.36',
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
