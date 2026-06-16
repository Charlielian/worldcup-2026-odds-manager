"""比赛与小组/队伍相关业务逻辑。"""
import itertools
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from sqlmodel import Session, select

from app.models.group import Group, Team
from app.models.match import Match, Odds
from app.utils.flags import get_flag

logger = logging.getLogger(__name__)


# ── 序列化（与旧 backend/db.py serialize_match 保持一致） ──────────

def serialize_match(match: Match, odds: Optional[Odds] = None) -> dict:
    """把 Match（+ 最新 Odds）转成 dict。"""
    result = {
        'id': match.id,
        'team1': match.team1,
        'team2': match.team2,
        'match_time': match.match_time,
        'stage': match.stage,
        'status': match.status,
        'score1': match.score1,
        'score2': match.score2,
        'group_name': match.group_name,
        'flag1': get_flag(match.team1),
        'flag2': get_flag(match.team2),
    }
    if odds is not None:
        result['odds'] = {
            'win_odds': odds.win_odds,
            'draw_odds': odds.draw_odds,
            'lose_odds': odds.lose_odds,
            'update_time': odds.update_time,
            'source': odds.source,
        }
    return result


def _latest_odds_subquery():
    """获取每场比赛最新赔率的子查询。"""
    return select(Odds).where(
        Odds.id == select(Odds.id)
        .where(Odds.match_id == Match.id)
        .order_by(Odds.update_time.desc(), Odds.id.desc())
        .limit(1)
        .scalar_subquery()
    )


def _match_with_latest_odds_query(stage_filter_sql: str, params: tuple = ()):
    """构建带最新赔率 JOIN 的查询。"""
    # 简化：使用子查询拉取最新 odds 字典
    stmt = select(Match)
    return stmt


def _rows_with_latest_odds(session: Session, matches: List[Match]) -> List[Tuple[Match, Optional[Odds]]]:
    """为每场比赛获取最新一条赔率。"""
    if not matches:
        return []
    ids = [m.id for m in matches]
    # 每个 match_id 取最新一条 odds
    subq = (
        select(Odds)
        .where(Odds.match_id.in_(ids))
        .order_by(Odds.match_id, Odds.update_time.desc(), Odds.id.desc())
    )
    rows = session.exec(subq).all()
    by_match: dict[int, Odds] = {}
    for o in rows:
        if o.match_id not in by_match:
            by_match[o.match_id] = o
    return [(m, by_match.get(m.id)) for m in matches]


def get_matches_by_date(session: Session, date: str) -> List[Tuple[Match, Optional[Odds]]]:
    """获取指定日期的比赛（用 LIKE match_time）。"""
    stmt = (
        select(Match)
        .where(Match.match_time.like(f"{date}%"))
        .order_by(Match.match_time, Match.id)
    )
    matches = session.exec(stmt).all()
    return _rows_with_latest_odds(session, matches)


def get_upcoming_matches(session: Session, start_date: str, days: int = 7) -> List[Tuple[Match, Optional[Odds]]]:
    end_date = (
        datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=days)
    ).strftime("%Y-%m-%d")
    stmt = (
        select(Match)
        .where(Match.match_time >= start_date)
        .where(Match.match_time < end_date)
        .order_by(Match.match_time, Match.id)
    )
    matches = session.exec(stmt).all()
    return _rows_with_latest_odds(session, matches)


def group_matches_by_date(matches: List[Tuple[Match, Optional[Odds]]]) -> dict:
    """按日期分组比赛。"""
    grouped: dict[str, list] = {}
    for m, o in matches:
        d = m.match_time.split(' ')[0]
        grouped.setdefault(d, []).append((m, o))
    return grouped


def get_next_match_date(session: Session) -> str:
    today = datetime.now().strftime("%Y-%m-%d")
    stmt = (
        select(Match.match_time)
        .where(Match.match_time >= today)
        .order_by(Match.match_time)
        .limit(1)
    )
    result = session.exec(stmt).first()
    if result:
        return result.split(' ')[0]
    return today


def get_group_matches(session: Session, group: Optional[str] = None) -> List[Tuple[Match, Optional[Odds]]]:
    if group:
        stmt = (
            select(Match)
            .where(Match.stage == '小组赛')
            .where(Match.group_name == f"{group}组")
            .order_by(Match.match_time, Match.id)
        )
    else:
        stmt = (
            select(Match)
            .where(Match.stage == '小组赛')
            .order_by(Match.match_time, Match.id)
        )
    matches = session.exec(stmt).all()
    return _rows_with_latest_odds(session, matches)


_KNOCKOUT_STAGE_ORDER = {
    '1/16决赛': 1, '1/8决赛': 2, '1/4决赛': 3,
    '半决赛': 4, '三四名决赛': 5, '决赛': 6, '淘汰赛': 7,
}


def get_knockout_matches(session: Session) -> List[Tuple[Match, Optional[Odds]]]:
    """淘汰赛比赛，按 round 排序。"""
    stages = list(_KNOCKOUT_STAGE_ORDER.keys())
    stmt = (
        select(Match)
        .where(Match.stage.in_(stages))
        .order_by(Match.match_time, Match.id)
    )
    matches = session.exec(stmt).all()
    matches_sorted = sorted(
        matches,
        key=lambda m: (_KNOCKOUT_STAGE_ORDER.get(m.stage, 99), m.match_time, m.id or 0),
    )
    return _rows_with_latest_odds(session, matches_sorted)


def get_all_group_matches(session: Session) -> List[Match]:
    stmt = (
        select(Match)
        .where(Match.stage == '小组赛')
        .order_by(Match.group_name, Match.match_time)
    )
    return list(session.exec(stmt).all())


def add_group_match(session: Session, team1: str, team2: str, match_time: str, group_name: str) -> None:
    m = Match(
        team1=team1, team2=team2, match_time=match_time,
        stage='小组赛', group_name=group_name,
    )
    session.add(m)
    session.commit()


def get_all_groups(session: Session) -> List[Group]:
    stmt = select(Group).order_by(Group.id)
    return list(session.exec(stmt).all())


def get_teams_by_group(session: Session, group_id: int) -> List[Team]:
    stmt = select(Team).where(Team.group_id == group_id).order_by(Team.id)
    return list(session.exec(stmt).all())


def add_team_to_group(session: Session, team_name: str, group_id: int) -> bool:
    stmt = select(Team).where(Team.group_id == group_id)
    if len(list(session.exec(stmt).all())) >= 4:
        return False
    t = Team(team_name=team_name, group_id=group_id)
    session.add(t)
    session.commit()
    return True


def delete_team(session: Session, team_id: int) -> None:
    t = session.get(Team, team_id)
    if t:
        session.delete(t)
        session.commit()


def generate_group_matches(session: Session, group_id: int, group_name: str) -> None:
    stmt = select(Team).where(Team.group_id == group_id)
    teams = [t.team_name for t in session.exec(stmt).all()]
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    for t1, t2 in itertools.combinations(teams, 2):
        session.add(Match(
            team1=t1, team2=t2, match_time=now_str,
            stage='小组赛', group_name=group_name,
        ))
    session.commit()


def get_match_by_id(session: Session, match_id: int) -> Optional[Match]:
    return session.get(Match, match_id)


def update_match_info(
    session: Session, match_id: int, team1: str, team2: str,
    match_time: str, group_name: str, status: str,
    score1, score2,
) -> None:
    m = session.get(Match, match_id)
    if not m:
        return
    m.team1 = team1
    m.team2 = team2
    m.match_time = match_time
    m.group_name = group_name
    m.status = status
    m.score1 = score1
    m.score2 = score2
    session.add(m)
    session.commit()


def update_match_result(session: Session, match_id: int, score1, score2) -> None:
    m = session.get(Match, match_id)
    if not m:
        return
    m.status = 'finished'
    m.score1 = score1
    m.score2 = score2
    session.add(m)
    session.commit()


def get_group_name_by_id(session: Session, group_id: int) -> Optional[str]:
    g = session.get(Group, group_id)
    return g.group_name if g else None
