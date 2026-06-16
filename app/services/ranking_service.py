"""小组排名与最佳第三名计算。"""
import logging
from typing import List, Optional

from sqlmodel import Session, select

from app.models.group import Group, Team
from app.models.match import Match
from app.utils.normalize import normalize_team_name

logger = logging.getLogger(__name__)


def get_group_rankings(session: Session, group: Optional[str] = None) -> list:
    """获取小组排名。"""
    teams = list(session.exec(select(Team)).all())
    finished = list(session.exec(
        select(Match.team1, Match.team2, Match.score1, Match.score2, Match.group_name)
        .where(Match.status == 'finished')
        .where(Match.stage == '小组赛')
    ).all())

    group_rows = list(session.exec(select(Group).order_by(Group.id)).all())
    gid_to_name = {g.id: g.group_name for g in group_rows}
    name_to_gid = {g.group_name: g.id for g in group_rows}

    team_stats: dict[str, dict] = {}
    for t in teams:
        normalized = normalize_team_name(t.team_name)
        team_stats[normalized] = {
            'team_id': t.id,
            'team_name': normalized,
            'flag': getattr(t, 'flag', '') or '',
            'group_id': t.group_id,
            'played': 0,
            'won': 0,
            'drawn': 0,
            'lost': 0,
            'goals_for': 0,
            'goals_against': 0,
            'goal_difference': 0,
            'points': 0,
        }

    for t1, t2, s1, s2, gname in finished:
        s1v = int(s1) if s1 else 0
        s2v = int(s2) if s2 else 0
        nt1 = normalize_team_name(t1)
        nt2 = normalize_team_name(t2)
        current_gid = name_to_gid.get(gname, 1)

        if nt1 not in team_stats:
            team_stats[nt1] = {
                'team_id': 0, 'team_name': nt1, 'flag': '', 'group_id': current_gid,
                'played': 0, 'won': 0, 'drawn': 0, 'lost': 0,
                'goals_for': 0, 'goals_against': 0, 'goal_difference': 0, 'points': 0,
            }
        if nt2 not in team_stats:
            team_stats[nt2] = {
                'team_id': 0, 'team_name': nt2, 'flag': '', 'group_id': current_gid,
                'played': 0, 'won': 0, 'drawn': 0, 'lost': 0,
                'goals_for': 0, 'goals_against': 0, 'goal_difference': 0, 'points': 0,
            }

        s = team_stats[nt1]
        s['played'] += 1
        s['goals_for'] += s1v
        s['goals_against'] += s2v
        s['goal_difference'] = s['goals_for'] - s['goals_against']
        if s1v > s2v:
            s['won'] += 1; s['points'] += 3
        elif s1v == s2v:
            s['drawn'] += 1; s['points'] += 1
        else:
            s['lost'] += 1

        s = team_stats[nt2]
        s['played'] += 1
        s['goals_for'] += s2v
        s['goals_against'] += s1v
        s['goal_difference'] = s['goals_for'] - s['goals_against']
        if s2v > s1v:
            s['won'] += 1; s['points'] += 3
        elif s2v == s1v:
            s['drawn'] += 1; s['points'] += 1
        else:
            s['lost'] += 1

    grouped: dict[int, list] = {}
    for tn, s in team_stats.items():
        grouped.setdefault(s['group_id'], []).append(s)

    for gid, group_teams in grouped.items():
        group_teams.sort(key=lambda x: (-x['points'], -x['goal_difference'], -x['goals_for']))

    result = []
    for gid in sorted(grouped.keys()):
        gname = gid_to_name.get(gid, f'Group {gid}')
        if group and gname != f"{group}组":
            continue
        result.append({
            'group_id': gid,
            'group_name': gname,
            'teams': grouped[gid],
        })
    return result


def get_best_third_place_teams(rankings: list) -> dict:
    """根据 rankings 计算最佳第三名映射。"""
    third_place_teams = []
    for grp in rankings:
        if len(grp['teams']) >= 3:
            tp = grp['teams'][2]
            tp = dict(tp)
            tp['group_name'] = grp['group_name'].replace('组', '')
            third_place_teams.append(tp)

    third_place_teams.sort(key=lambda x: (-x['points'], -x['goal_difference'], -x['goals_for']))

    mapping: dict = {}
    for i in range(min(8, len(third_place_teams))):
        mapping[f'最佳小组第三({i+1})'] = third_place_teams[i]['team_name']

    for label, groups_for in [
        ('C3/E3/F3/G3', ['C', 'E', 'F', 'G']),
        ('A3/C3/D3/H3', ['A', 'C', 'D', 'H']),
        ('B3/F3/G3/I3', ['B', 'F', 'G', 'I']),
        ('D3/E3/H3/I3/L3', ['D', 'E', 'H', 'I', 'L']),
        ('F3/G3/H3/I3/J3', ['F', 'G', 'H', 'I', 'J']),
        ('H3/I3/J3/K3/L3', ['H', 'I', 'J', 'K', 'L']),
    ]:
        eligible = [t for t in third_place_teams if t['group_name'] in groups_for]
        if eligible:
            mapping[label] = eligible[0]['team_name']

    return mapping


def get_group_team_mapping(session: Session) -> dict:
    rankings = get_group_rankings(session)
    mapping: dict = {}
    for grp in rankings:
        letter = grp['group_name'].replace('组', '')
        for idx, team in enumerate(grp['teams'], 1):
            mapping[f'{letter}{idx}'] = team['team_name']
    mapping.update(get_best_third_place_teams(rankings))
    return mapping


def is_group_stage_completed(session: Session) -> bool:
    unfinished = list(session.exec(
        select(Match.id).where(Match.stage == '小组赛').where(Match.status != 'finished')
    ).all())
    return len(unfinished) == 0
