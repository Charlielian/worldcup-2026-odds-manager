"""中国体彩（sporttery.cn）赔率数据源。"""
import logging
import requests
from typing import List, Optional, Dict, Any

from app.services.odds_base import OddsProvider, OddsData
from app.utils.flags import get_team_icon

logger = logging.getLogger(__name__)

BASE_URL = "https://webapi.sporttery.cn/gateway/jc/football"

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

BQC_MAP = {
    'h_h': '胜-胜', 'h_d': '胜-平', 'h_a': '胜-负',
    'd_h': '平-胜', 'd_d': '平-平', 'd_a': '平-负',
    'a_h': '负-胜', 'a_d': '负-平', 'a_a': '负-负',
}


class SportteryProvider(OddsProvider):
    """中国体彩竞彩足球赔率数据源。"""

    def fetch_odds(self) -> List[OddsData]:
        try:
            batch = self._fetch_page(1, self.config.get('page_size', 100))
            logger.info(f"[{self.name}] 共获取 {len(batch)} 条赔率")
            return batch
        except Exception as e:
            logger.error(f"[{self.name}] 抓取失败: {e}")
            return []

    def fetch_all_play_types(self) -> List[Dict[str, Any]]:
        pool_code = self.config.get('pool_code', 'had,hhad,crs,ttg,bqc')
        try:
            matches = self._fetch_page_full(1, self.config.get('page_size', 100), pool_code)
            logger.info(f"[{self.name}] 共获取 {len(matches)} 场比赛（全玩法）")
            return matches
        except Exception as e:
            logger.error(f"[{self.name}] 抓取失败: {e}")
            return []

    def _fetch_page(self, page: int, page_size: int) -> List[OddsData]:
        pool_code = self.config.get('pool_code', 'had,hhad')
        url = (
            f"{BASE_URL}/getMatchCalculatorV1.qry?"
            f"poolCode={pool_code}&channel=c"
            f"&matchPage={page}&pageSize={page_size}"
        )
        headers = dict(DEFAULT_HEADERS)
        headers.update(self.config.get('extra_headers', {}))
        proxies = self.config.get('proxies')

        response = requests.get(
            url, headers=headers,
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
            for match in day_group.get('subMatchList', []):
                try:
                    odds = self._parse_match(match)
                    if odds:
                        result.append(odds)
                except Exception as e:
                    logger.warning(f"[{self.name}] 解析失败: {match.get('matchNumStr', '?')} - {e}")
        return result

    def _fetch_page_full(self, page: int, page_size: int, pool_code: str) -> List[Dict]:
        url = (
            f"{BASE_URL}/getMatchCalculatorV1.qry?"
            f"poolCode={pool_code}&channel=c"
            f"&matchPage={page}&pageSize={page_size}"
        )
        headers = dict(DEFAULT_HEADERS)
        headers.update(self.config.get('extra_headers', {}))
        proxies = self.config.get('proxies')

        response = requests.get(
            url, headers=headers,
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
            for match in day_group.get('subMatchList', []):
                try:
                    parsed = self._parse_match_full(match)
                    if parsed:
                        result.append(parsed)
                except Exception as e:
                    logger.warning(f"[{self.name}] 解析失败: {match.get('matchNumStr', '?')} - {e}")
        return result

    def _parse_match(self, match: dict) -> Optional[OddsData]:
        if match.get('matchStatus') != 'Selling':
            return None

        had = match.get('had', {})
        if not had or not had.get('h'):
            return None

        home_team = match.get('homeTeamAbbName', '')
        away_team = match.get('awayTeamAbbName', '')
        if not home_team or not away_team:
            return None

        update_date = had.get('updateDate', '')
        update_time = had.get('updateTime', '')
        updated_at = f"{update_date} {update_time}" if update_date else ''

        return OddsData(
            team1=home_team,
            team2=away_team,
            win_odds=float(had['h']),
            draw_odds=float(had['d']),
            lose_odds=float(had['a']),
            source=self.name,
            updated_at=updated_at,
        )

    def _parse_match_full(self, match: dict) -> Optional[Dict]:
        if match.get('matchStatus') != 'Selling':
            return None

        had = match.get('had', {})
        hhad = match.get('hhad', {})
        crs = match.get('crs', {})
        ttg = match.get('ttg', {})
        bqc = match.get('bqc', {})

        home_team = match.get('homeTeamAbbName', '')
        away_team = match.get('awayTeamAbbName', '')
        if not home_team or not away_team:
            return None

        home_icon = get_team_icon(home_team)
        away_icon = get_team_icon(away_team)

        update_date = had.get('updateDate', '')
        update_time = had.get('updateTime', '')
        updated_at = f"{update_date} {update_time}" if update_date else ''

        had_data = None
        if had and had.get('h'):
            had_data = {
                'win': float(had['h']),
                'draw': float(had['d']),
                'lose': float(had['a']),
                'update_time': updated_at,
            }

        hhad_data = None
        if hhad and hhad.get('h'):
            hhad_data = {
                'win': float(hhad['h']),
                'draw': float(hhad['d']),
                'lose': float(hhad['a']),
                'goal_line': hhad.get('goalLine', ''),
                'update_time': f"{hhad.get('updateDate', '')} {hhad.get('updateTime', '')}".strip(),
            }

        crs_list = []
        if crs:
            for key, value in crs.items():
                if not value:
                    continue
                if not key.startswith('s'):
                    continue
                try:
                    parts = key.split('s')
                    parts = [p for p in parts if p]
                    if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                        score = f"{int(parts[0])}:{int(parts[1])}"
                        odds_val = float(value)
                        crs_list.append({'score': score, 'odds': odds_val})
                except (IndexError, ValueError):
                    continue
            crs_list.sort(key=lambda x: (int(x['score'].split(':')[0]), int(x['score'].split(':')[1])))

        ttg_list = []
        if ttg:
            for key, value in ttg.items():
                if not value or not key.startswith('s'):
                    continue
                try:
                    rest = key[1:]
                    if rest.isdigit():
                        goals = int(rest)
                        odds_val = float(value)
                        ttg_list.append({'goals': goals, 'label': f'{goals}球', 'odds': odds_val})
                except ValueError:
                    continue
            ttg_list.sort(key=lambda x: x['goals'])

        bqc_list = []
        if bqc:
            for key, value in bqc.items():
                if key in BQC_MAP and value:
                    try:
                        bqc_list.append({
                            'code': key,
                            'result': BQC_MAP[key],
                            'odds': float(value),
                        })
                    except ValueError:
                        continue
            bqc_list.sort(key=lambda x: x['code'])

        return {
            'match_num': match.get('matchNumStr', ''),
            'league': match.get('leagueAbbName', ''),
            'home_team': home_team,
            'away_team': away_team,
            'home_icon': home_icon,
            'away_icon': away_icon,
            'match_date': match.get('matchDate', ''),
            'match_time': match.get('matchTime', ''),
            'home_rank': match.get('homeRank', ''),
            'away_rank': match.get('awayRank', ''),
            'had': had_data,
            'hhad': hhad_data,
            'crs': crs_list,
            'ttg': ttg_list,
            'bqc': bqc_list,
            'source': self.name,
            'updated_at': updated_at,
        }

    def fetch_match_results(self, start_date: str, end_date: str) -> List[dict]:
        url = (
            f"{BASE_URL}/getMatchResultV1.qry?"
            f"matchPage=1&pcOrWap=1&leagueId="
            f"&matchBeginDate={start_date}&matchEndDate={end_date}"
        )
        headers = dict(DEFAULT_HEADERS)
        try:
            response = requests.get(
                url, headers=headers,
                timeout=self.config.get('timeout', 30),
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
