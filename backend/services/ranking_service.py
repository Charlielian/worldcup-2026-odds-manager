import logging
from sqlite3 import Error

from backend.db import db_pool
from backend.utils.normalize import normalize_team_name

logger = logging.getLogger(__name__)


def get_group_rankings(group=None):
    """获取小组排名。"""
    conn = db_pool.get_connection()
    try:
        cursor = conn.cursor()

        # 获取所有队伍
        cursor.execute("SELECT id, team_name, group_id FROM teams")
        teams = cursor.fetchall()

        # 获取所有已结束的比赛
        cursor.execute("SELECT team1, team2, score1, score2, group_name FROM matches WHERE status = 'finished' AND stage = '小组赛'")
        finished_matches = cursor.fetchall()

        # 初始化队伍统计数据
        team_stats = {}
        for team in teams:
            team_id, team_name, group_id = team
            normalized_name = normalize_team_name(team_name)
            team_stats[normalized_name] = {
                'team_id': team_id,
                'team_name': normalized_name,
                'group_id': group_id,
                'played': 0,
                'won': 0,
                'drawn': 0,
                'lost': 0,
                'goals_for': 0,
                'goals_against': 0,
                'goal_difference': 0,
                'points': 0
            }

        # 计算每场比赛的统计数据
        for match in finished_matches:
            team1, team2, score1, score2, group_name = match
            score1 = int(score1) if score1 else 0
            score2 = int(score2) if score2 else 0

            normalized_team1 = normalize_team_name(team1)
            normalized_team2 = normalize_team_name(team2)

            # 获取当前比赛的group_id
            cursor.execute("SELECT id FROM groups WHERE group_name = ?", (group_name,))
            group_result = cursor.fetchone()
            current_group_id = group_result[0] if group_result else 1

            # 确保队伍1在team_stats中
            if normalized_team1 not in team_stats:
                cursor.execute("SELECT group_id FROM teams WHERE team_name = ?", (normalized_team1,))
                result = cursor.fetchone()
                group_id = result[0] if result else current_group_id
                team_stats[normalized_team1] = {
                    'team_id': 0,
                    'team_name': normalized_team1,
                    'group_id': group_id,
                    'played': 0,
                    'won': 0,
                    'drawn': 0,
                    'lost': 0,
                    'goals_for': 0,
                    'goals_against': 0,
                    'goal_difference': 0,
                    'points': 0
                }

            # 更新队伍1的统计数据
            team_stats[normalized_team1]['played'] += 1
            team_stats[normalized_team1]['goals_for'] += score1
            team_stats[normalized_team1]['goals_against'] += score2
            team_stats[normalized_team1]['goal_difference'] = team_stats[normalized_team1]['goals_for'] - team_stats[normalized_team1]['goals_against']

            if score1 > score2:
                team_stats[normalized_team1]['won'] += 1
                team_stats[normalized_team1]['points'] += 3
            elif score1 == score2:
                team_stats[normalized_team1]['drawn'] += 1
                team_stats[normalized_team1]['points'] += 1
            else:
                team_stats[normalized_team1]['lost'] += 1

            # 确保队伍2在team_stats中
            if normalized_team2 not in team_stats:
                cursor.execute("SELECT group_id FROM teams WHERE team_name = ?", (normalized_team2,))
                result = cursor.fetchone()
                group_id = result[0] if result else current_group_id
                team_stats[normalized_team2] = {
                    'team_id': 0,
                    'team_name': normalized_team2,
                    'group_id': group_id,
                    'played': 0,
                    'won': 0,
                    'drawn': 0,
                    'lost': 0,
                    'goals_for': 0,
                    'goals_against': 0,
                    'goal_difference': 0,
                    'points': 0
                }

            # 更新队伍2的统计数据
            team_stats[normalized_team2]['played'] += 1
            team_stats[normalized_team2]['goals_for'] += score2
            team_stats[normalized_team2]['goals_against'] += score1
            team_stats[normalized_team2]['goal_difference'] = team_stats[normalized_team2]['goals_for'] - team_stats[normalized_team2]['goals_against']

            if score2 > score1:
                team_stats[normalized_team2]['won'] += 1
                team_stats[normalized_team2]['points'] += 3
            elif score2 == score1:
                team_stats[normalized_team2]['drawn'] += 1
                team_stats[normalized_team2]['points'] += 1
            else:
                team_stats[normalized_team2]['lost'] += 1

        # 按小组分组
        grouped_stats = {}
        for team_name, stats in team_stats.items():
            group_id = stats['group_id']
            if group_id not in grouped_stats:
                grouped_stats[group_id] = []
            grouped_stats[group_id].append(stats)

        # 对每个小组的队伍按积分排序
        for group_id, group_teams in grouped_stats.items():
            group_teams.sort(key=lambda x: (-x['points'], -x['goal_difference'], -x['goals_for']))

        # 获取小组名称
        cursor.execute("SELECT id, group_name FROM groups")
        groups = {id: name for id, name in cursor.fetchall()}

        # 组合小组名称和排名
        result = []
        for group_id, group_teams in grouped_stats.items():
            group_name = groups.get(group_id, f'Group {group_id}')
            if group and group_name != group + '组':
                continue
            result.append({
                'group_id': group_id,
                'group_name': group_name,
                'teams': group_teams
            })

        # 按小组ID排序
        result.sort(key=lambda x: x['group_id'])

        return result
    except Error as e:
        logger.error("get_group_rankings 错误: %s", e)
        return []
    finally:
        db_pool.return_connection(conn)


def get_best_third_place_teams():
    """获取成绩最好的小组第三。"""
    rankings = get_group_rankings()
    third_place_teams = []

    # 收集所有小组的第三名
    for group in rankings:
        if len(group['teams']) >= 3:
            third_place = group['teams'][2]  # 索引2是第三名
            third_place['group_name'] = group['group_name'].replace('组', '')
            third_place_teams.append(third_place)

    # 按规则排序：1. 积分 2. 净胜球 3. 总进球数
    third_place_teams.sort(key=lambda x: (-x['points'], -x['goal_difference'], -x['goals_for']))

    # 生成映射，包括最佳小组第三(1)到(8)
    mapping = {}

    # 处理最佳小组第三(1)到(8)
    for i in range(min(8, len(third_place_teams))):
        mapping[f'最佳小组第三({i+1})'] = third_place_teams[i]['team_name']

    # 处理 C3/E3/F3/G3
    groups_for_c3 = ['C', 'E', 'F', 'G']
    eligible_teams = [t for t in third_place_teams if t['group_name'] in groups_for_c3]
    if eligible_teams:
        best_team = eligible_teams[0]
        mapping['C3/E3/F3/G3'] = best_team['team_name']

    # 处理 A3/C3/D3/H3
    groups_for_a3 = ['A', 'C', 'D', 'H']
    eligible_teams = [t for t in third_place_teams if t['group_name'] in groups_for_a3]
    if eligible_teams:
        best_team = eligible_teams[0]
        mapping['A3/C3/D3/H3'] = best_team['team_name']

    # 处理 B3/F3/G3/I3
    groups_for_b3 = ['B', 'F', 'G', 'I']
    eligible_teams = [t for t in third_place_teams if t['group_name'] in groups_for_b3]
    if eligible_teams:
        best_team = eligible_teams[0]
        mapping['B3/F3/G3/I3'] = best_team['team_name']

    # 处理 D3/E3/H3/I3/L3
    groups_for_d3 = ['D', 'E', 'H', 'I', 'L']
    eligible_teams = [t for t in third_place_teams if t['group_name'] in groups_for_d3]
    if eligible_teams:
        best_team = eligible_teams[0]
        mapping['D3/E3/H3/I3/L3'] = best_team['team_name']

    # 处理 F3/G3/H3/I3/J3
    groups_for_f3 = ['F', 'G', 'H', 'I', 'J']
    eligible_teams = [t for t in third_place_teams if t['group_name'] in groups_for_f3]
    if eligible_teams:
        best_team = eligible_teams[0]
        mapping['F3/G3/H3/I3/J3'] = best_team['team_name']

    # 处理 H3/I3/J3/K3/L3
    groups_for_h3 = ['H', 'I', 'J', 'K', 'L']
    eligible_teams = [t for t in third_place_teams if t['group_name'] in groups_for_h3]
    if eligible_teams:
        best_team = eligible_teams[0]
        mapping['H3/I3/J3/K3/L3'] = best_team['team_name']

    return mapping


def get_group_team_mapping():
    """获取小组排名的队伍名称映射。"""
    rankings = get_group_rankings()
    mapping = {}

    for group in rankings:
        group_name = group['group_name'].replace('组', '')
        for idx, team in enumerate(group['teams'], 1):
            mapping[f'{group_name}{idx}'] = team['team_name']

    # 处理小组第三的比较逻辑
    mapping.update(get_best_third_place_teams())

    return mapping


def is_group_stage_completed():
    """检查小组赛是否全部完成。"""
    conn = db_pool.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM matches WHERE stage = '小组赛' AND status != 'finished'")
        unfinished_count = cursor.fetchone()[0]
        return unfinished_count == 0
    except Error as e:
        logger.error("is_group_stage_completed 错误: %s", e)
        return False
    finally:
        db_pool.return_connection(conn)
