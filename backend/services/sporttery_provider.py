"""
中国体彩（sporttery.cn）赔率数据源
对接体彩官方 API: webapi.sporttery.cn

支持玩法:
- HAD:   胜平负（非让球）
- HHAD:  让球胜平负
- CRS:   比分
- TTG:   总进球
- BQC:   半全场
"""
import logging
import requests
import time
from typing import List, Optional, Dict, Any
from backend.services.odds_base import OddsProvider, OddsData

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


class SportteryProvider(OddsProvider):
    """
    中国体彩竞彩足球赔率数据源
    支持胜平负、让球胜平负、比分、总进球、半全场全部玩法
    """

    def fetch_odds(self) -> List[OddsData]:
        """抓取体彩在售比赛的赔率数据（胜平负基础数据）"""
        all_odds = []
        page = 1
        page_size = self.config.get('page_size', 100)

        while True:
            try:
                batch = self._fetch_page(page, page_size)
                if not batch:
                    break
                all_odds.extend(batch)
                if len(batch) < page_size:
                    break
                page += 1
                time.sleep(self.config.get('page_delay', 1.0))
            except Exception as e:
                logger.error(f"[{self.name}] 抓取第 {page} 页失败: {e}")
                break

        logger.info(f"[{self.name}] 共获取 {len(all_odds)} 条赔率")
        return all_odds

    def fetch_all_play_types(self) -> List[Dict[str, Any]]:
        """抓取所有玩法的赔率（胜平负/让球/比分/总进球/半全场）"""
        all_matches = []
        page = 1
        page_size = self.config.get('page_size', 100)
        pool_code = self.config.get('pool_code', 'had,hhad,crs,ttg,bqc')

        while True:
            url = (
                f"{BASE_URL}/getMatchCalculatorV1.qry?"
                f"poolCode={pool_code}&channel=c"
                f"&matchPage={page}&pageSize={page_size}"
            )
            headers = dict(DEFAULT_HEADERS)
            headers.update(self.config.get('extra_headers', {}))
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
                    logger.warning(f"[{self.name}] API 返回错误: {data.get('errorMessage')}")
                    break

                match_info_list = data.get('value', {}).get('matchInfoList', [])
                if not match_info_list:
                    break

                for day_group in match_info_list:
                    for match in day_group.get('subMatchList', []):
                        try:
                            parsed = self._parse_all_play_types(match)
                            if parsed:
                                all_matches.append(parsed)
                        except Exception as e:
                            logger.warning(f"[{self.name}] 解析比赛失败: {e}")
                            continue

                if len(all_matches) < page * page_size:
                    break
                page += 1
                time.sleep(self.config.get('page_delay', 1.0))

            except Exception as e:
                logger.error(f"[{self.name}] 抓取全部玩法失败: {e}")
                break

        logger.info(f"[{self.name}] 共获取 {len(all_matches)} 场完整赔率数据")
        return all_matches

    def _fetch_page(self, page: int, page_size: int) -> List[OddsData]:
        """抓取单页数据（胜平负基础赔率）"""
        pool_code = self.config.get('pool_code', 'had,hhad')
        url = (
            f"{BASE_URL}/getMatchCalculatorV1.qry?"
            f"poolCode={pool_code}&channel=c"
            f"&matchPage={page}&pageSize={page_size}"
        )

        headers = dict(DEFAULT_HEADERS)
        headers.update(self.config.get('extra_headers', {}))
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
                        logger.warning(f"[{self.name}] 解析比赛失败: {e}")
                        continue

            return result

        except Exception as e:
            logger.error(f"[{self.name}] 抓取第 {page} 页失败: {e}")
            return []

    def _parse_match(self, match: dict) -> Optional[OddsData]:
        """解析单场比赛基础赔率"""
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

    def _parse_all_play_types(self, match: dict) -> Optional[Dict[str, Any]]:
        """解析所有玩法的赔率数据"""
        if match.get('matchStatus') != 'Selling':
            return None

        home_team = match.get('homeTeamAbbName', '')
        away_team = match.get('awayTeamAbbName', '')
        if not home_team or not away_team:
            return None

        result = {
            'match_num': match.get('matchNumStr', ''),
            'match_date': match.get('matchDate', ''),
            'match_time': match.get('matchTime', ''),
            'home_team': home_team,
            'away_team': away_team,
            'league': match.get('leagueAbbName', ''),
            'match_status': match.get('matchStatus', ''),
            'had': None,
            'hhad': None,
            'crs': None,
            'ttg': None,
            'bqc': None,
        }

        # 胜平负 HAD
        had = match.get('had', {})
        if had and had.get('h'):
            update_dt = ''
            ud = had.get('updateDate', '')
            ut = had.get('updateTime', '')
            if ud:
                update_dt = f"{ud} {ut}" if ut else ud
            result['had'] = {
                'win': float(had['h']),
                'draw': float(had['d']),
                'lose': float(had['a']),
                'update_time': update_dt,
            }

        # 让球胜平负 HHAD
        hhad = match.get('hhad', {})
        if hhad and hhad.get('h'):
            update_dt = ''
            ud = hhad.get('updateDate', '')
            ut = hhad.get('updateTime', '')
            if ud:
                update_dt = f"{ud} {ut}" if ut else ud
            result['hhad'] = {
                'goal_line': hhad.get('goalLine', ''),
                'win': float(hhad['h']),
                'draw': float(hhad['d']),
                'lose': float(hhad['a']),
                'update_time': update_dt,
            }

        # 比分 CRS
        crs = match.get('crs', {})
        if crs and crs.get('h'):
            update_dt = ''
            ud = crs.get('updateDate', '')
            ut = crs.get('updateTime', '')
            if ud:
                update_dt = f"{ud} {ut}" if ut else ud
            result['crs'] = {
                'scores': {
                    '0:0': float(crs.get('h0h0', 0)) or None,
                    '0:1': float(crs.get('h0a1', 0)) or None,
                    '0:2': float(crs.get('h0a2', 0)) or None,
                    '0:3': float(crs.get('h0a3', 0)) or None,
                    '0:4': float(crs.get('h0a4', 0)) or None,
                    '1:0': float(crs.get('h1h0', 0)) or None,
                    '1:1': float(crs.get('h1h1', 0)) or None,
                    '1:2': float(crs.get('h1a1', 0)) or None,
                    '1:3': float(crs.get('h1a2', 0)) or None,
                    '1:4': float(crs.get('h1a3', 0)) or None,
                    '2:0': float(crs.get('h2h0', 0)) or None,
                    '2:1': float(crs.get('h2h1', 0)) or None,
                    '2:2': float(crs.get('h2h2', 0)) or None,
                    '2:3': float(crs.get('h2a1', 0)) or None,
                    '2:4': float(crs.get('h2a2', 0)) or None,
                    '3:0': float(crs.get('h3h0', 0)) or None,
                    '3:1': float(crs.get('h3h1', 0)) or None,
                    '3:2': float(crs.get('h3h2', 0)) or None,
                    '3:3': float(crs.get('h3h3', 0)) or None,
                    '3:4': float(crs.get('h3a1', 0)) or None,
                    '4:0': float(crs.get('h4h0', 0)) or None,
                    '4:1': float(crs.get('h4h1', 0)) or None,
                    '4:2': float(crs.get('h4h2', 0)) or None,
                    '4:3': float(crs.get('h4h3', 0)) or None,
                    '4:4': float(crs.get('h4h4', 0)) or None,
                    '胜其他': float(crs.get('h999', 0)) or None,
                    '0:5': float(crs.get('h0a5', 0)) or None,
                    '5:0': float(crs.get('h5h0', 0)) or None,
                    '负其他': float(crs.get('a999', 0)) or None,
                },
                'update_time': update_dt,
            }

        # 总进球 TTG
        ttg = match.get('TTG', {})
        if ttg:
            update_dt = ''
            ud = ttg.get('updateDate', '')
            ut = ttg.get('updateTime', '')
            if ud:
                update_dt = f"{ud} {ut}" if ut else ud
            result['ttg'] = {
                'total_0': float(ttg.get('s0', 0)) or None,
                'total_1': float(ttg.get('s1', 0)) or None,
                'total_2': float(ttg.get('s2', 0)) or None,
                'total_3': float(ttg.get('s3', 0)) or None,
                'total_4': float(ttg.get('s4', 0)) or None,
                'total_5': float(ttg.get('s5', 0)) or None,
                'total_6': float(ttg.get('s6', 0)) or None,
                'total_7': float(ttg.get('s7', 0)) or None,
                'update_time': update_dt,
            }

        # 半全场 BQC
        bqc = match.get('bqc', {})
        if bqc and bqc.get('hh'):
            update_dt = ''
            ud = bqc.get('updateDate', '')
            ut = bqc.get('updateTime', '')
            if ud:
                update_dt = f"{ud} {ut}" if ut else ud
            result['bqc'] = {
                'win_win': float(bqc['hh']) or None,
                'win_draw': float(bqc['hd']) or None,
                'win_lose': float(bqc['ha']) or None,
                'draw_win': float(bqc['dh']) or None,
                'draw_draw': float(bqc['dd']) or None,
                'draw_lose': float(bqc['da']) or None,
                'lose_win': float(bqc['ah']) or None,
                'lose_draw': float(bqc['ad']) or None,
                'lose_lose': float(bqc['aa']) or None,
                'update_time': update_dt,
            }

        # 至少需要有胜平负数据
        if not result['had']:
            return None

        return result

    def fetch_match_results(self, start_date: str, end_date: str) -> List[dict]:
        """抓取比赛结果"""
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
