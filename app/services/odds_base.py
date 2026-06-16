"""赔率数据源抽象基类和数据结构。"""
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List

logger = logging.getLogger(__name__)


@dataclass
class OddsData:
    team1: str
    team2: str
    win_odds: float
    draw_odds: float
    lose_odds: float
    source: str
    updated_at: str


class OddsProvider(ABC):
    def __init__(self, name: str, config: dict):
        self.name = name
        self.config = config
        self.enabled = config.get('enabled', True)
        self.priority = config.get('priority', 1)

    @abstractmethod
    def fetch_odds(self) -> List[OddsData]:
        pass

    def _get_headers(self) -> dict:
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.0.36',
            'Accept': 'application/json, text/html, */*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
