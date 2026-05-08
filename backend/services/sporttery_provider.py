"""
中国体彩（sporttery.cn）赔率数据源
对接体彩官方 API: webapi.sporttery.cn

支持玩法:
- HAD:  胜平负（非让球）
- HHAD: 让球胜平负

API 接口:
- 可售比赛赔率: getMatchCalculatorV1.qry
- 比赛结果:     getMatchResultV1.qry
"""
import logging
import requests
import time
from typing import List, Optional
from backend.services.odds_base import OddsProvider, OddsData

logger = logging.getLogger(__name__)

# 体彩 API 基础地址
BASE_URL = "https://webapi.sporttery.cn/gateway/jc/football"

# 默认请求头（模拟移动端）
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) "
        "AppleWebKit/605.1.15 (KHTML, like Gecko) "
        "Version/16.0 Mobile/15E148 Safari/604.1"
    ),
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Referer": "https://m.sporttery.cn/mjc/jsq/zqspf/",
    "X-Requested-With": "XMLHttpRequest",
}


class SportteryProvider(OddsProvider):
    """
    中国体彩竞彩足球赔率数据源

    从 sporttery.cn 官方 API 获取当前在售比赛的胜平负赔率。
    数据包含: 胜平负(HAD) 和 让球胜平负(HHAD) 两种玩法。
    """

    def fetch_odds(self) -> List[OddsData]:
        """抓取体彩在售比赛的赔率数据"""
        all_odds = []

        # 分页抓取所有在售比赛
        page = 1
        page_size = self.config.get('page_size', 100)

        while True:
            try:
                batch = self._fetch_page(page, page_size)
                if not batch:
                    break
                all_odds.extend(batch)

                # 如果返回数量小于页大小，说明已到最后一页
                if len(batch) < page_size:
                    break

                page += 1
                # 请求间隔，避免触发反爬
                time.sleep(self.config.get('page_delay', 1.0))

            except Exception as e:
                logger.error(f"[{self.name}] 抓取第 {page} 页失败: {e}")
                break

        logger.info(f"[{self.name}] 共获取 {len(all_odds)} 条赔率")
        return all_odds

    def _fetch_page(self, page: int, page_size: int) -> List[OddsData]:
        """抓取单页数据"""
        pool_code = self.config.get('pool_code', 'had,hhad')
        url = (
            f"{BASE_URL}/getMatchCalculatorV1.qry?"
            f"poolCode={pool_code}&channel=c"
            f"&matchPage={page}&pageSize={page_size}"
        )

        headers = dict(DEFAULT_HEADERS)
        headers.update(self.config.get('extra_headers', {}))

        # 支持自定义代理
        proxies = self.config.get('proxies')

        response = requests.get(
            url,
            headers=headers,
            timeout=self.config.get('timeout', 30),
            proxies=proxies,
        )
        response.raise_for_status()
        data = response.json()

        if not data.get('success'):
            logger.warning(f"[{self.name}] API 返回错误: {data.get('errorMessage')}")
            return []

        match_info_list = data.get('value', {}).get('matchInfoList', [])
        if not match_info_list:
            return []

        result = []
        for day_group in match_info_list:
            sub_matches = day_group.get('subMatchList', [])
            for match in sub_matches:
                try:
                    odds = self._parse_match(match)
                    if odds:
                        result.append(odds)
                except Exception as e:
                    logger.warning(
                        f"[{self.name}] 解析比赛失败: "
                        f"{match.get('matchNumStr', '?')} - {e}"
                    )
                    continue

        return result

    def _parse_match(self, match: dict) -> Optional[OddsData]:
        """
        解析单场比赛数据

        API 返回结构:
        - had.h / had.d / had.a  → 胜平负赔率
        - hhad.h / hhad.d / hhad.a → 让球胜平负赔率
        - hhad.goalLine → 让球数 (如 "+1", "-1")
        - homeTeamAbbName → 主队简称
        - awayTeamAbbName → 客队简称
        - leagueAbbName → 联赛简称
        - matchNumStr → 比赛编号 (如 "周五001")
        - matchDate / matchTime → 比赛日期时间
        """
        # 只处理在售中的比赛
        if match.get('matchStatus') != 'Selling':
            return None

        # 提取胜平负赔率 (HAD)
        had = match.get('had', {})
        if not had or not had.get('h'):
            return None

        home_team = match.get('homeTeamAbbName', '')
        away_team = match.get('awayTeamAbbName', '')

        if not home_team or not away_team:
            return None

        # 获取更新时间
        update_date = had.get('updateDate', '')
        update_time = had.get('updateTime', '')
        updated_at = f"{update_date} {update_time}" if update_date else ''

        # 让球胜平负信息 (HHAD)
        hhad = match.get('hhad', {})
        let_ball = hhad.get('goalLine', '')

        odds_data = OddsData(
            team1=home_team,
            team2=away_team,
            win_odds=float(had['h']),
            draw_odds=float(had['d']),
            lose_odds=float(had['a']),
            source=self.name,
            updated_at=updated_at,
        )

        return odds_data

    def fetch_match_results(self, start_date: str, end_date: str) -> List[dict]:
        """
        抓取比赛结果（历史比分）

        Args:
            start_date: 开始日期 "YYYY-MM-DD"
            end_date: 结束日期 "YYYY-MM-DD"

        Returns:
            比赛结果列表，每项包含:
            - match_num: 比赛编号
            - home_team: 主队
            - away_team: 客队
            - score: 比分
            - win_flag: 胜平负结果 (H/D/A)
            - let_ball: 让球数
            - league: 联赛
        """
        url = (
            f"{BASE_URL}/getMatchResultV1.qry?"
            f"matchPage=1&pcOrWap=1&leagueId="
            f"&matchBeginDate={start_date}&matchEndDate={end_date}"
        )

        headers = dict(DEFAULT_HEADERS)
        proxies = self.config.get('proxies')

        try:
            response = requests.get(
                url, headers=headers,
                timeout=self.config.get('timeout', 30),
                proxies=proxies,
            )
            response.raise_for_status()
            data = response.json()

            if not data.get('success'):
                logger.warning(f"[{self.name}] 获取比赛结果失败: {data.get('errorMessage')}")
                return []

            results = data.get('value', {}).get('matchResult', [])
            logger.info(f"[{self.name}] 获取 {len(results)} 条比赛结果")
            return results

        except Exception as e:
            logger.error(f"[{self.name}] 获取比赛结果异常: {e}")
            return []
