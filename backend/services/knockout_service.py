import logging
from sqlite3 import Error

import backend.db
from backend.utils.flags import get_flag
from backend.services.ranking_service import (
    get_group_team_mapping,
    is_group_stage_completed,
)

logger = logging.getLogger(__name__)


def init_knockout_matchups():
    """初始化淘汰赛对阵表（32强）。"""
    conn = backend.db.db_pool.get_connection()
    try:
        cursor = conn.cursor()

        # 检查是否已有数据
        cursor.execute("SELECT COUNT(*) FROM knockout_matchups")
        if cursor.fetchone()[0] > 0:
            # 清空现有数据，重新初始化
            cursor.execute("DELETE FROM knockout_matchups")

        # 32强对阵数据
        knockout_data = [
            # 1/16决赛 (1-16) - 16场
            (1, '1/16决赛', 'r16_1', 'A1', '最佳小组第三(1)', '墨西哥城', '2026-06-28 03:00'),
            (2, '1/16决赛', 'r16_2', 'B1', '最佳小组第三(2)', '多伦多', '2026-06-28 10:00'),
            (3, '1/16决赛', 'r16_3', 'C1', '最佳小组第三(3)', '亚特兰大', '2026-06-28 15:00'),
            (4, '1/16决赛', 'r16_4', 'D1', '最佳小组第三(4)', '旧金山', '2026-06-28 20:00'),
            (5, '1/16决赛', 'r16_5', 'E1', 'F2', '西雅图', '2026-06-29 03:00'),
            (6, '1/16决赛', 'r16_6', 'F1', 'E2', '费城', '2026-06-29 10:00'),
            (7, '1/16决赛', 'r16_7', 'G1', 'H2', '休斯顿', '2026-06-29 15:00'),
            (8, '1/16决赛', 'r16_8', 'H1', 'G2', '洛杉矶', '2026-06-29 20:00'),
            (9, '1/16决赛', 'r16_9', 'I1', '最佳小组第三(5)', '迈阿密', '2026-06-30 03:00'),
            (10, '1/16决赛', 'r16_10', 'J1', '最佳小组第三(6)', '堪萨斯城', '2026-06-30 10:00'),
            (11, '1/16决赛', 'r16_11', 'K1', '最佳小组第三(7)', '达拉斯', '2026-06-30 15:00'),
            (12, '1/16决赛', 'r16_12', 'L1', '最佳小组第三(8)', '波士顿', '2026-06-30 20:00'),
            (13, '1/16决赛', 'r16_13', 'A2', 'B2', '温哥华', '2026-07-01 03:00'),
            (14, '1/16决赛', 'r16_14', 'C2', 'D2', '纽约/新泽西', '2026-07-01 10:00'),
            (15, '1/16决赛', 'r16_15', 'I2', 'J2', '芝加哥', '2026-07-01 15:00'),
            (16, '1/16决赛', 'r16_16', 'K2', 'L2', '蒙特利尔', '2026-07-01 20:00'),
            # 1/8决赛 (17-24) - 8场
            (17, '1/8决赛', 'r8_1', '1胜者', '3胜者', '费城', '2026-07-04 03:00'),
            (18, '1/8决赛', 'r8_2', '2胜者', '5胜者', '休斯顿', '2026-07-04 10:00'),
            (19, '1/8决赛', 'r8_3', '4胜者', '6胜者', '洛杉矶', '2026-07-05 03:00'),
            (20, '1/8决赛', 'r8_4', '7胜者', '9胜者', '迈阿密', '2026-07-05 10:00'),
            (21, '1/8决赛', 'r8_5', '8胜者', '10胜者', '堪萨斯城', '2026-07-06 03:00'),
            (22, '1/8决赛', 'r8_6', '11胜者', '13胜者', '达拉斯', '2026-07-06 10:00'),
            (23, '1/8决赛', 'r8_7', '12胜者', '14胜者', '波士顿', '2026-07-07 03:00'),
            (24, '1/8决赛', 'r8_8', '15胜者', '16胜者', '亚特兰大', '2026-07-07 10:00'),
            # 1/4决赛 (25-28) - 4场
            (25, '1/4决赛', 'qf_1', '17胜者', '18胜者', '波士顿', '2026-07-09 03:00'),
            (26, '1/4决赛', 'qf_2', '19胜者', '20胜者', '洛杉矶', '2026-07-09 10:00'),
            (27, '1/4决赛', 'qf_3', '21胜者', '22胜者', '迈阿密', '2026-07-10 03:00'),
            (28, '1/4决赛', 'qf_4', '23胜者', '24胜者', '堪萨斯城', '2026-07-10 10:00'),
            # 半决赛 (29-30) - 2场
            (29, '半决赛', 'sf_1', '25胜者', '26胜者', '达拉斯', '2026-07-14 03:00'),
            (30, '半决赛', 'sf_2', '27胜者', '28胜者', '亚特兰大', '2026-07-15 03:00'),
            # 三四名决赛
            (31, '三四名决赛', 'third_place', '29负者', '30负者', '迈阿密', '2026-07-19 05:00'),
            # 决赛
            (32, '决赛', 'final', '29胜者', '30胜者', '纽约/新泽西', '2026-07-20 08:00'),
        ]

        cursor.executemany(
            "INSERT INTO knockout_matchups (match_number, round_name, position, slot1_team_group, slot2_team_group, venue, match_time) VALUES (?, ?, ?, ?, ?, ?, ?)",
            knockout_data
        )

        conn.commit()
    except Error as e:
        logger.error("init_knockout_matchups 错误: %s", e)
        conn.rollback()
    finally:
        backend.db.db_pool.return_connection(conn)


def update_knockout_teams():
    """更新淘汰赛对阵表中的实际队伍。"""
    if not is_group_stage_completed():
        return

    conn = backend.db.db_pool.get_connection()
    try:
        cursor = conn.cursor()

        team_mapping = get_group_team_mapping()

        cursor.execute("SELECT id, slot1_team_group, slot2_team_group FROM knockout_matchups")
        matchups = cursor.fetchall()

        for matchup in matchups:
            match_id, slot1, slot2 = matchup

            team1 = team_mapping.get(slot1, slot1)
            team2 = team_mapping.get(slot2, slot2)

            # 更新matches表中的实际队伍名称
            match_time = None
            cursor.execute("SELECT match_time FROM knockout_matchups WHERE id = ?", (match_id,))
            result = cursor.fetchone()
            if result:
                match_time = result[0]

            # 查找或创建淘汰赛比赛记录
            cursor.execute("SELECT id FROM matches WHERE match_time = ? AND stage = '淘汰赛'", (match_time,))
            existing_match = cursor.fetchone()

            if existing_match:
                cursor.execute(
                    "UPDATE matches SET team1 = ?, team2 = ? WHERE id = ?",
                    (team1, team2, existing_match[0])
                )
            else:
                cursor.execute(
                    "INSERT INTO matches (team1, team2, match_time, stage, status) VALUES (?, ?, ?, ?, ?)",
                    (team1, team2, match_time, '淘汰赛', 'upcoming')
                )

        conn.commit()
    except Error as e:
        logger.error("update_knockout_teams 错误: %s", e)
        conn.rollback()
    finally:
        backend.db.db_pool.return_connection(conn)


def get_knockout_bracket_data():
    """获取淘汰赛对阵数据（用于赛程图）。"""
    conn = backend.db.db_pool.get_connection()
    try:
        cursor = conn.cursor()

        # 获取队伍映射，即使小组赛未完成也能获取基本映射
        team_mapping = {}
        if is_group_stage_completed():
            team_mapping = get_group_team_mapping()

        cursor.execute("SELECT id, match_number, round_name, position, slot1_team_group, slot2_team_group, venue, match_time FROM knockout_matchups ORDER BY match_number")
        matchups = cursor.fetchall()

        bracket_data = []
        for matchup in matchups:
            match_id, match_number, round_name, position, slot1, slot2, venue, match_time = matchup

            # 处理小组第三的映射
            if slot1 in team_mapping:
                team1 = team_mapping[slot1]
            elif not slot1.endswith('胜者') and not slot1.endswith('负者'):
                team1 = slot1
            else:
                team1 = slot1

            if slot2 in team_mapping:
                team2 = team_mapping[slot2]
            elif not slot2.endswith('胜者') and not slot2.endswith('负者'):
                team2 = slot2
            else:
                team2 = slot2

            flag1 = get_flag(team1)
            flag2 = get_flag(team2)

            bracket_data.append({
                'id': match_id,
                'match_number': match_number,
                'round_name': round_name,
                'position': position,
                'team1': team1,
                'team2': team2,
                'flag1': flag1,
                'flag2': flag2,
                'venue': venue,
                'match_time': match_time,
                'slot1_team_group': slot1,
                'slot2_team_group': slot2
            })

        return bracket_data
    except Error as e:
        logger.error("get_knockout_bracket_data 错误: %s", e)
        return []
    finally:
        backend.db.db_pool.return_connection(conn)
