import logging
import itertools
from datetime import datetime, timedelta
from sqlite3 import Error

import backend.db
from backend.db import get_matches_with_odds_joined

logger = logging.getLogger(__name__)


def init_db():
    """初始化数据库表结构和示例数据。"""
    conn = backend.db.get_connection()
    try:
        cursor = conn.cursor()

        # 读取schema.sql文件创建表
        with open('schema.sql', 'r', encoding='utf-8') as f:
            schema = f.read()
        cursor.executescript(schema)

        # 插入小组数据
        cursor.execute("SELECT COUNT(*) FROM groups")
        if cursor.fetchone()[0] == 0:
            groups = [("A组",), ("B组",), ("C组",), ("D组",), ("E组",), ("F组",), ("G组",), ("H组",), ("I组",), ("J组",), ("K组",), ("L组",)]
            cursor.executemany("INSERT INTO groups (group_name) VALUES (?)", groups)

        # 插入示例队伍数据
        cursor.execute("SELECT COUNT(*) FROM teams")
        if cursor.fetchone()[0] == 0:
            # A组队伍
            teams_a = [("墨西哥", 1), ("南非", 1), ("韩国", 1), ("欧洲附加赛D组胜者", 1)]
            # B组队伍
            teams_b = [("加拿大", 2), ("欧洲附加赛A组胜者", 2), ("卡塔尔", 2), ("瑞士", 2)]
            # C组队伍
            teams_c = [("巴西", 3), ("摩洛哥", 3), ("海地", 3), ("苏格兰", 3)]
            # D组队伍
            teams_d = [("美国", 4), ("巴拉圭", 4), ("澳大利亚", 4), ("欧洲附加赛C组胜者", 4)]
            # E组队伍
            teams_e = [("德国", 5), ("库拉索", 5), ("科特迪瓦", 5), ("厄瓜多尔", 5)]
            # F组队伍
            teams_f = [("荷兰", 6), ("日本", 6), ("欧洲附加赛B组胜者", 6), ("突尼斯", 6)]
            # G组队伍
            teams_g = [("比利时", 7), ("埃及", 7), ("伊朗", 7), ("新西兰", 7)]
            # H组队伍
            teams_h = [("西班牙", 8), ("佛得角", 8), ("沙特阿拉伯", 8), ("乌拉圭", 8)]
            # I组队伍
            teams_i = [("法国", 9), ("塞内加尔", 9), ("洲际附加赛2组胜者", 9), ("挪威", 9)]
            # J组队伍
            teams_j = [("阿根廷", 10), ("阿尔及利亚", 10), ("奥地利", 10), ("约旦", 10)]
            # K组队伍
            teams_k = [("葡萄牙", 11), ("洲际附加赛1组胜者", 11), ("乌兹别克斯坦", 11), ("哥伦比亚", 11)]
            # L组队伍
            teams_l = [("英格兰", 12), ("克罗地亚", 12), ("加纳", 12), ("巴拿马", 12)]

            cursor.executemany("INSERT INTO teams (team_name, group_id) VALUES (?, ?)", teams_a + teams_b + teams_c + teams_d + teams_e + teams_f + teams_g + teams_h + teams_i + teams_j + teams_k + teams_l)

        # 插入示例比赛数据
        cursor.execute("SELECT COUNT(*) FROM matches")
        if cursor.fetchone()[0] == 0:
            # 小组赛数据
            group_matches = [
                ("巴西", "塞尔维亚", "2026-06-15 18:00", "小组赛", "A组"),
                ("法国", "澳大利亚", "2026-06-16 15:00", "小组赛", "B组"),
                ("阿根廷", "沙特阿拉伯", "2026-06-17 21:00", "小组赛", "C组"),
                ("英格兰", "伊朗", "2026-06-18 18:00", "小组赛", "D组"),
                ("德国", "日本", "2026-06-19 15:00", "小组赛", "E组"),
                ("比利时", "加拿大", "2026-06-20 21:00", "小组赛", "F组")
            ]

            # 淘汰赛数据
            knockout_matches = [
                ("巴西", "墨西哥", "2026-07-01 21:00", "淘汰赛"),
                ("法国", "波兰", "2026-07-02 18:00", "淘汰赛"),
                ("阿根廷", "厄瓜多尔", "2026-07-03 15:00", "淘汰赛"),
                ("英格兰", "塞内加尔", "2026-07-04 21:00", "淘汰赛")
            ]

            # 插入小组赛
            cursor.executemany(
                "INSERT INTO matches (team1, team2, match_time, stage, group_name) VALUES (?, ?, ?, ?, ?)",
                group_matches
            )

            # 插入淘汰赛
            cursor.executemany(
                "INSERT INTO matches (team1, team2, match_time, stage) VALUES (?, ?, ?, ?)",
                knockout_matches
            )

        conn.commit()
    except Error as e:
        logger.error("init_db 错误: %s", e)
        conn.rollback()
    finally:
        backend.db.db_pool.return_connection(conn)


def get_matches_by_date(date):
    """获取指定日期的比赛（使用 JOIN 优化，避免 N+1 查询）。"""
    conn = backend.db.db_pool.get_connection()
    try:
        cursor = conn.cursor()
        return get_matches_with_odds_joined(
            cursor,
            "match_time LIKE ?",
            (date + '%',)
        )
    except Error as e:
        logger.error("get_matches_by_date 错误: %s", e)
        return []
    finally:
        backend.db.db_pool.return_connection(conn)


def get_upcoming_matches(start_date, days=7):
    """获取从指定日期开始的未来比赛（使用 JOIN 优化）。"""
    conn = backend.db.db_pool.get_connection()
    try:
        cursor = conn.cursor()
        end_date = (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=days)).strftime("%Y-%m-%d")
        return get_matches_with_odds_joined(
            cursor,
            "match_time >= ? AND match_time < ?",
            (start_date, end_date)
        )
    except Error as e:
        logger.error("get_upcoming_matches 错误: %s", e)
        return []
    finally:
        backend.db.db_pool.return_connection(conn)


def group_matches_by_date(matches):
    """按日期分组比赛。"""
    grouped = {}
    for match, odds in matches:
        match_date = match[3].split(' ')[0]
        if match_date not in grouped:
            grouped[match_date] = []
        grouped[match_date].append((match, odds))
    return grouped


def get_next_match_date():
    """获取最近有比赛的日期。"""
    conn = backend.db.db_pool.get_connection()
    try:
        cursor = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cursor.execute(
            "SELECT DISTINCT DATE(match_time) as match_date FROM matches WHERE match_time >= ? ORDER BY match_date LIMIT 1",
            (today,)
        )
        result = cursor.fetchone()

        if result:
            return result[0]
        return today
    except Error as e:
        logger.error("get_next_match_date 错误: %s", e)
        return datetime.now().strftime("%Y-%m-%d")
    finally:
        backend.db.db_pool.return_connection(conn)


def get_group_matches(group=None):
    """获取小组赛比赛（使用 JOIN 优化）。"""
    conn = backend.db.db_pool.get_connection()
    try:
        cursor = conn.cursor()
        if group:
            return get_matches_with_odds_joined(
                cursor,
                "stage = '小组赛' AND group_name = ?",
                (group + '组',)
            )
        else:
            return get_matches_with_odds_joined(
                cursor,
                "stage = '小组赛'"
            )
    except Error as e:
        logger.error("get_group_matches 错误: %s", e)
        return []
    finally:
        backend.db.db_pool.return_connection(conn)


def get_knockout_matches():
    """获取所有淘汰赛比赛（使用 JOIN 优化，适配淘汰赛轮次排序）。

    注意：淘汰赛需要特殊排序（按轮次），不能直接使用 get_matches_with_odds_joined 的默认 ORDER BY。
    因此这里使用自定义 JOIN 查询。
    """
    from backend.services.ranking_service import is_group_stage_completed

    if not is_group_stage_completed():
        return []

    conn = backend.db.db_pool.get_connection()
    try:
        cursor = conn.cursor()

        query = """
            SELECT m.id, m.team1, m.team2, m.match_time, m.stage, m.status, m.score1, m.score2, m.group_name,
                   o.win_odds, o.draw_odds, o.lose_odds, o.update_time
            FROM matches m
            LEFT JOIN (
                SELECT match_id, win_odds, draw_odds, lose_odds, update_time
                FROM odds o1
                WHERE update_time = (SELECT MAX(update_time) FROM odds o2 WHERE o2.match_id = o1.match_id)
            ) o ON m.id = o.match_id
            LEFT JOIN knockout_matchups km ON m.match_time = km.match_time
            WHERE m.stage = '淘汰赛'
            ORDER BY
                CASE
                    WHEN km.round_name = '1/16决赛' THEN 1
                    WHEN km.round_name = '1/8决赛' THEN 2
                    WHEN km.round_name = '1/4决赛' THEN 3
                    WHEN km.round_name = '半决赛' THEN 4
                    WHEN km.round_name = '三四名决赛' THEN 5
                    WHEN km.round_name = '决赛' THEN 6
                    ELSE 7
                END, m.match_time
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        result = []
        for row in rows:
            match_tuple = (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8])
            odds_tuple = (row[9], row[10], row[11], row[12]) if row[9] is not None else None
            result.append((match_tuple, odds_tuple))

        return result
    except Error as e:
        logger.error("get_knockout_matches 错误: %s", e)
        return []
    finally:
        backend.db.db_pool.return_connection(conn)


def get_all_group_matches():
    """获取所有小组赛信息（用于管理页面）。"""
    conn = backend.db.db_pool.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, team1, team2, match_time, stage, group_name, status, score1, score2 FROM matches WHERE stage = '小组赛' ORDER BY group_name, match_time"
        )
        matches = cursor.fetchall()
        return matches
    except Error as e:
        logger.error("get_all_group_matches 错误: %s", e)
        return []
    finally:
        backend.db.db_pool.return_connection(conn)


def add_group_match(team1, team2, match_time, group_name):
    """添加小组赛信息。"""
    conn = backend.db.db_pool.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO matches (team1, team2, match_time, stage, group_name) VALUES (?, ?, ?, ?, ?)",
            (team1, team2, match_time, '小组赛', group_name)
        )
        conn.commit()
    except Error as e:
        logger.error("add_group_match 错误: %s", e)
        conn.rollback()
    finally:
        backend.db.db_pool.return_connection(conn)


def get_all_groups():
    """获取所有小组。"""
    conn = backend.db.db_pool.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, group_name FROM groups ORDER BY id")
        groups = cursor.fetchall()
        return groups
    except Error as e:
        logger.error("get_all_groups 错误: %s", e)
        return []
    finally:
        backend.db.db_pool.return_connection(conn)


def get_teams_by_group(group_id):
    """获取小组的所有队伍。"""
    conn = backend.db.db_pool.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id, team_name FROM teams WHERE group_id = ? ORDER BY id", (group_id,))
        teams = cursor.fetchall()
        return teams
    except Error as e:
        logger.error("get_teams_by_group 错误: %s", e)
        return []
    finally:
        backend.db.db_pool.return_connection(conn)


def add_team_to_group(team_name, group_id):
    """添加队伍到小组。"""
    conn = backend.db.db_pool.get_connection()
    try:
        cursor = conn.cursor()
        # 检查小组是否已经有4支队
        cursor.execute("SELECT COUNT(*) FROM teams WHERE group_id = ?", (group_id,))
        count = cursor.fetchone()[0]
        if count >= 4:
            return False

        cursor.execute(
            "INSERT INTO teams (team_name, group_id) VALUES (?, ?)",
            (team_name, group_id)
        )
        conn.commit()
        return True
    except Error as e:
        logger.error("add_team_to_group 错误: %s", e)
        conn.rollback()
        return False
    finally:
        backend.db.db_pool.return_connection(conn)


def delete_team(team_id):
    """删除队伍。"""
    conn = backend.db.db_pool.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM teams WHERE id = ?", (team_id,))
        conn.commit()
    except Error as e:
        logger.error("delete_team 错误: %s", e)
        conn.rollback()
    finally:
        backend.db.db_pool.return_connection(conn)


def generate_group_matches(group_id, group_name):
    """为小组生成比赛。"""
    conn = backend.db.db_pool.get_connection()
    try:
        cursor = conn.cursor()
        # 获取小组的所有队伍
        cursor.execute("SELECT team_name FROM teams WHERE group_id = ?", (group_id,))
        teams = [row[0] for row in cursor.fetchall()]

        # 生成两两队伍的比赛
        matches = list(itertools.combinations(teams, 2))

        # 插入比赛到数据库
        for team1, team2 in matches:
            match_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            cursor.execute(
                "INSERT INTO matches (team1, team2, match_time, stage, group_name) VALUES (?, ?, ?, ?, ?)",
                (team1, team2, match_time, '小组赛', group_name)
            )

        conn.commit()
    except Error as e:
        logger.error("generate_group_matches 错误: %s", e)
        conn.rollback()
    finally:
        backend.db.db_pool.return_connection(conn)


def get_match_by_id(match_id):
    """获取单个比赛信息。"""
    conn = backend.db.db_pool.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, team1, team2, match_time, stage, group_name, status, score1, score2 FROM matches WHERE id = ?",
            (match_id,)
        )
        match = cursor.fetchone()
        return match
    except Error as e:
        logger.error("get_match_by_id 错误: %s", e)
        return None
    finally:
        backend.db.db_pool.return_connection(conn)


def update_match_info(match_id, team1, team2, match_time, group_name, status, score1, score2):
    """更新比赛信息。"""
    conn = backend.db.db_pool.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE matches SET team1 = ?, team2 = ?, match_time = ?, group_name = ?, status = ?, score1 = ?, score2 = ? WHERE id = ?",
            (team1, team2, match_time, group_name, status, score1, score2, match_id)
        )
        conn.commit()
    except Error as e:
        logger.error("update_match_info 错误: %s", e)
        conn.rollback()
    finally:
        backend.db.db_pool.return_connection(conn)


def update_match_result(match_id, score1, score2):
    """更新比赛结果。"""
    conn = backend.db.db_pool.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE matches SET status = 'finished', score1 = ?, score2 = ? WHERE id = ?",
            (score1, score2, match_id)
        )
        conn.commit()
    except Error as e:
        logger.error("update_match_result 错误: %s", e)
        conn.rollback()
    finally:
        backend.db.db_pool.return_connection(conn)


def get_group_name_by_id(group_id):
    """根据小组ID获取小组名称（使用连接池）。"""
    conn = backend.db.db_pool.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT group_name FROM groups WHERE id = ?", (group_id,))
        result = cursor.fetchone()
        return result[0] if result else None
    except Error as e:
        logger.error("get_group_name_by_id 错误: %s", e)
        return None
    finally:
        backend.db.db_pool.return_connection(conn)
