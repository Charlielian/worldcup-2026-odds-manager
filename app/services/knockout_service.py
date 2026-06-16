"""淘汰赛业务逻辑（对阵初始化、对阵图、槽位解析）。"""
import logging
from typing import List, Optional, Tuple

from sqlmodel import Session, select

from app.models.group import Group, Team
from app.models.knockout import KnockoutMatchup
from app.models.match import Match
from app.services.knockout_schema import KNOCKOUT
from app.services.ranking_service import (
    get_group_team_mapping, is_group_stage_completed,
)
from app.utils.flags import get_flag

logger = logging.getLogger(__name__)


def init_knockout_matchups(session: Session) -> None:
    """初始化淘汰赛对阵表（32强）。"""
    # 清空旧表
    existing = list(session.exec(select(KnockoutMatchup)).all())
    for e in existing:
        session.delete(e)
    session.commit()

    # 重新插入
    for (mn, rnd, pos, code, s1, s2, a1, a2, mt, stage, t1, t2, venue) in KNOCKOUT:
        allowed = None
        if a1 or a2:
            allowed = ";".join(filter(None, [a1 or "", a2 or ""]))
        session.add(KnockoutMatchup(
            match_number=mn, round_name=rnd, position=pos,
            slot1_team_group=s1, slot2_team_group=s2,
            venue=venue, match_time=mt,
            bracket_code=code, allowed_third_groups=allowed,
        ))
    session.commit()
    logger.info("淘汰赛对阵表初始化完成: %d 条", len(KNOCKOUT))


def update_knockout_teams(session: Session) -> None:
    """小组赛结束后，把 slot1/slot2 里 'X组第N' 解析为具体国家队。"""
    if not is_group_stage_completed(session):
        return

    team_mapping = get_group_team_mapping(session)
    matchups = list(session.exec(select(KnockoutMatchup)).all())
    for ko in matchups:
        s1 = ko.slot1_team_group
        s2 = ko.slot2_team_group

        if s1 in team_mapping:
            t1 = team_mapping[s1]
        elif s1 == "TBD_3RD":
            t1 = "待定小组第三名"
        else:
            t1 = s1

        if s2 in team_mapping:
            t2 = team_mapping[s2]
        elif s2 == "TBD_3RD":
            t2 = "待定小组第三名"
        else:
            t2 = s2

        if not ko.match_time:
            continue
        existing_match = session.exec(
            select(Match)
            .where(Match.match_time == ko.match_time)
            .where(Match.stage.in_(['1/16决赛', '1/8决赛', '1/4决赛', '半决赛', '三四名决赛', '决赛']))
        ).first()
        if existing_match:
            existing_match.team1 = t1
            existing_match.team2 = t2
            session.add(existing_match)
        else:
            session.add(Match(
                team1=t1, team2=t2, match_time=ko.match_time,
                stage=ko.round_name, status='upcoming',
            ))
    session.commit()


def _resolve_slot(slot: Optional[str], allowed_third: Optional[str],
                  team_mapping: dict, best_thirds: list) -> str:
    if not slot:
        return ""
    if slot in team_mapping:
        return team_mapping[slot]
    if slot == "TBD_3RD":
        if allowed_third and best_thirds:
            groups = [g.strip() for g in allowed_third.split(",") if g.strip()]
            for g_name, t_name in best_thirds:
                if g_name in groups:
                    return t_name
        return "待定小组第三名"
    return slot


def _get_group_rankings_lite(session: Session) -> list:
    """精简版小组排名。"""
    groups = list(session.exec(select(Group)).all())
    teams = list(session.exec(select(Team)).all())
    finished = list(session.exec(
        select(Match.team1, Match.team2, Match.score1, Match.score2, Match.group_name)
        .where(Match.status == 'finished')
        .where(Match.stage == '小组赛')
    ).all())

    stats: dict[str, dict] = {}
    for t in teams:
        stats[t.team_name] = {
            'team_name': t.team_name, 'group_id': t.group_id,
            'points': 0, 'goal_difference': 0, 'goals_for': 0,
        }

    gid_to_letter = {g.id: g.group_name.replace('组', '') for g in groups}

    for t1, t2, s1, s2, _ in finished:
        s1v = int(s1) if s1 else 0
        s2v = int(s2) if s2 else 0
        if t1 in stats:
            stats[t1]['goals_for'] += s1v
            stats[t1]['goal_difference'] += s1v - s2v
            if s1v > s2v:
                stats[t1]['points'] += 3
            elif s1v == s2v:
                stats[t1]['points'] += 1
        if t2 in stats:
            stats[t2]['goals_for'] += s2v
            stats[t2]['goal_difference'] += s2v - s1v
            if s2v > s1v:
                stats[t2]['points'] += 3
            elif s1v == s2v:
                stats[t2]['points'] += 1

    by_group: dict[str, list] = {}
    for t_name, s in stats.items():
        letter = gid_to_letter.get(s['group_id'], "?")
        by_group.setdefault(letter, []).append(s)

    result = []
    for letter, members in by_group.items():
        members.sort(key=lambda x: (-x['points'], -x['goal_difference'], -x['goals_for']))
        result.append({'letter': letter, 'teams': members})
    return result


def get_knockout_bracket_data(session: Session) -> list:
    """获取淘汰赛对阵数据。"""
    team_mapping: dict = {}
    best_thirds: list = []
    if is_group_stage_completed(session):
        team_mapping = get_group_team_mapping(session)
        for grp in _get_group_rankings_lite(session):
            if len(grp['teams']) >= 3:
                best_thirds.append((grp['letter'], grp['teams'][2]['team_name']))

    match_results: dict = {}
    matches = list(session.exec(
        select(Match)
        .where(Match.stage.in_(['1/16决赛', '1/8决赛', '1/4决赛', '半决赛', '三四名决赛', '决赛']))
    ).all())
    for m in matches:
        key = (m.match_time, m.team1, m.team2)
        match_results[key] = {
            'id': m.id, 'status': m.status, 'score1': m.score1, 'score2': m.score2,
        }

    matchups = list(session.exec(
        select(KnockoutMatchup).order_by(KnockoutMatchup.match_number)
    ).all())

    bracket_data = []
    for ko in matchups:
        allowed = ko.allowed_third_groups or ""
        parts = allowed.split(";")
        allowed1 = parts[0].strip() if len(parts) >= 1 and parts[0] else None
        allowed2 = parts[1].strip() if len(parts) >= 2 and parts[1] else None

        team1 = _resolve_slot(ko.slot1_team_group, allowed1, team_mapping, best_thirds)
        team2 = _resolve_slot(ko.slot2_team_group, allowed2, team_mapping, best_thirds)

        result = match_results.get((ko.match_time, team1, team2), {})
        status = result.get('status', 'upcoming')
        s1 = result.get('score1') or 0
        s2 = result.get('score2') or 0

        bracket_data.append({
            'id': ko.id,
            'match_id': result.get('id'),
            'match_number': ko.match_number,
            'round_name': ko.round_name,
            'position': ko.position,
            'bracket_code': ko.bracket_code,
            'team1': team1,
            'team2': team2,
            'flag1': get_flag(team1),
            'flag2': get_flag(team2),
            'venue': ko.venue,
            'match_time': ko.match_time,
            'slot1_team_group': ko.slot1_team_group,
            'slot2_team_group': ko.slot2_team_group,
            'status': status,
            'score1': s1,
            'score2': s2,
        })
    return bracket_data
