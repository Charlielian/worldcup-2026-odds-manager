from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_cors import CORS
import sqlite3
from sqlite3 import Error
from datetime import datetime, timedelta
import crawler
import threading
import time
import queue

# ============================================================
# 数据库连接池
# ============================================================
class DatabaseConnectionPool:
    def __init__(self, db_path, max_connections=5):
        self.db_path = db_path
        self.max_connections = max_connections
        self.connections = queue.Queue(max_connections)

        # 初始化连接池
        for _ in range(max_connections):
            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                self.connections.put(conn)
            except Error as e:
                print(f"Error creating database connection: {e}")

    def get_connection(self):
        return self.connections.get()

    def return_connection(self, conn):
        if conn:
            self.connections.put(conn)

    def close_all(self):
        while not self.connections.empty():
            try:
                conn = self.connections.get()
                conn.close()
            except Error as e:
                print(f"Error closing database connection: {e}")

# 初始化数据库连接池
db_pool = DatabaseConnectionPool('worldcup.db')

# ============================================================
# 国旗映射字典
# ============================================================
flag_map = {
    # 国家/地区: 国旗Unicode
    '墨西哥': '🇲🇽',
    '南非': '🇿🇦',
    '韩国': '🇰🇷',
    '欧洲附加赛D组胜者': '🏆',
    '加拿大': '🇨🇦',
    '欧洲附加赛A组胜者': '🏆',
    '卡塔尔': '🇶🇦',
    '瑞士': '🇨🇭',
    '巴西': '🇧🇷',
    '摩洛哥': '🇲🇦',
    '海地': '🇭🇹',
    '苏格兰': '🏴',
    '美国': '🇺🇸',
    '巴拉圭': '🇵🇾',
    '澳大利亚': '🇦🇺',
    '欧洲附加赛C组胜者': '🏆',
    '德国': '🇩🇪',
    '库拉索': '🇨🇼',
    '科特迪瓦': '🇨🇮',
    '厄瓜多尔': '🇪🇨',
    '荷兰': '🇳🇱',
    '日本': '🇯🇵',
    '欧洲附加赛B组胜者': '🏆',
    '突尼斯': '🇹🇳',
    '比利时': '🇧🇪',
    '埃及': '🇪🇬',
    '伊朗': '🇮🇷',
    '新西兰': '🇳🇿',
    '西班牙': '🇪🇸',
    '佛得角': '🇨🇻',
    '沙特阿拉伯': '🇸🇦',
    '乌拉圭': '🇺🇾',
    '法国': '🇫🇷',
    '塞内加尔': '🇸🇳',
    '洲际附加赛2组胜者': '🏆',
    '挪威': '🇳🇴',
    '阿根廷': '🇦🇷',
    '阿尔及利亚': '🇩🇿',
    '奥地利': '🇦🇹',
    '约旦': '🇯🇴',
    '葡萄牙': '🇵🇹',
    '洲际附加赛1组胜者': '🏆',
    '乌兹别克斯坦': '🇺🇿',
    '哥伦比亚': '🇨🇴',
    '英格兰': '🏴',
    '克罗地亚': '🇭🇷',
    '加纳': '🇬🇭',
    '巴拿马': '🇵🇦'
}

# 获取队伍的国旗
def get_flag(team_name):
    return flag_map.get(team_name, '')

# ============================================================
# Flask 应用初始化 & CORS 配置
# ============================================================
app = Flask(__name__)
CORS(app)  # 全局启用 CORS

# ============================================================
# 辅助函数：序列化工具
# ============================================================
def row_to_dict(row, columns):
    """将 sqlite3.Row 对象转换为字典。

    Args:
        row: sqlite3.Row 实例
        columns: 列名列表

    Returns:
        dict
    """
    if row is None:
        return None
    return {col: row[col] for col in columns}


def serialize_match(match_tuple, odds_tuple=None):
    """将比赛元组转换为干净的字典。

    match_tuple 期望顺序: (id, team1, team2, match_time, stage, status, score1, score2, group_name)
    odds_tuple 期望顺序: (win_odds, draw_odds, lose_odds, update_time)

    Returns:
        dict
    """
    result = {
        'id': match_tuple[0],
        'team1': match_tuple[1],
        'team2': match_tuple[2],
        'match_time': match_tuple[3],
        'stage': match_tuple[4],
        'status': match_tuple[5],
        'score1': match_tuple[6],
        'score2': match_tuple[7],
        'group_name': match_tuple[8] if len(match_tuple) > 8 else None,
        'flag1': get_flag(match_tuple[1]),
        'flag2': get_flag(match_tuple[2]),
    }

    if odds_tuple:
        result['odds'] = {
            'win_odds': odds_tuple[0],
            'draw_odds': odds_tuple[1],
            'lose_odds': odds_tuple[2],
            'update_time': odds_tuple[3],
        }

    return result


# ============================================================
# 初始化数据库
# ============================================================
def init_db():
    conn = db_pool.get_connection()
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
        print(f"Error in init_db: {e}")
        conn.rollback()
    finally:
        db_pool.return_connection(conn)

# ============================================================
# 业务逻辑函数（保持不变）
# ============================================================

# 获取指定日期的比赛
def get_matches_by_date(date):
    conn = db_pool.get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, team1, team2, match_time, stage, status, score1, score2, group_name FROM matches WHERE match_time LIKE ? ORDER BY match_time",
            (date + '%',)
        )
        matches = cursor.fetchall()

        # 获取每个比赛的最新赔率
        matches_with_odds = []
        for match in matches:
            match_id = match[0]
            cursor.execute(
                "SELECT win_odds, draw_odds, lose_odds, update_time FROM odds WHERE match_id = ? ORDER BY update_time DESC LIMIT 1",
                (match_id,)
            )
            odds = cursor.fetchone()
            matches_with_odds.append((match, odds))

        return matches_with_odds
    except Error as e:
        print(f"Error in get_matches_by_date: {e}")
        return []
    finally:
        db_pool.return_connection(conn)

# 获取往后的赛程（从指定日期开始的未来比赛）
def get_upcoming_matches(start_date, days=7):
    conn = db_pool.get_connection()
    try:
        cursor = conn.cursor()

        # 计算结束日期
        end_date = (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=days)).strftime("%Y-%m-%d")

        cursor.execute(
            "SELECT id, team1, team2, match_time, stage, status, score1, score2, group_name FROM matches WHERE match_time >= ? AND match_time < ? ORDER BY match_time",
            (start_date, end_date)
        )
        matches = cursor.fetchall()

        # 获取每个比赛的最新赔率
        matches_with_odds = []
        for match in matches:
            match_id = match[0]
            cursor.execute(
                "SELECT win_odds, draw_odds, lose_odds, update_time FROM odds WHERE match_id = ? ORDER BY update_time DESC LIMIT 1",
                (match_id,)
            )
            odds = cursor.fetchone()
            matches_with_odds.append((match, odds))

        return matches_with_odds
    except Error as e:
        print(f"Error in get_upcoming_matches: {e}")
        return []
    finally:
        db_pool.return_connection(conn)

# 按日期分组比赛
def group_matches_by_date(matches):
    grouped = {}
    for match, odds in matches:
        match_date = match[3].split(' ')[0]
        if match_date not in grouped:
            grouped[match_date] = []
        grouped[match_date].append((match, odds))
    return grouped

# 获取最近有比赛的日期
def get_next_match_date():
    conn = db_pool.get_connection()
    try:
        cursor = conn.cursor()

        # 获取所有未来的比赛，按日期排序
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
        print(f"Error in get_next_match_date: {e}")
        return datetime.now().strftime("%Y-%m-%d")
    finally:
        db_pool.return_connection(conn)

# 获取小组排名
def get_group_rankings(group=None):
    conn = db_pool.get_connection()
    try:
        cursor = conn.cursor()

        # 获取所有队伍
        cursor.execute("SELECT id, team_name, group_id FROM teams")
        teams = cursor.fetchall()

        # 获取所有已结束的比赛
        cursor.execute("SELECT team1, team2, score1, score2, group_name FROM matches WHERE status = 'finished' AND stage = '小组赛'")
        finished_matches = cursor.fetchall()

        # 标准化队伍名称的函数
        def normalize_team_name(name):
            # 处理不同格式的队伍名称
            name = name.strip()  # 去除首尾空格
            # 处理欧洲附加赛的不同格式
            if '欧洲' in name and '附加赛' in name and '胜者' in name:
                # 提取组号
                import re
                # 匹配任何字母或数字
                group_match = re.search(r'[A-Za-z0-9]', name)
                if group_match:
                    group = group_match.group()
                    return f'欧洲附加赛{group}组胜者'
            # 处理洲际附加赛的不同格式
            elif '洲际' in name and '附加赛' in name and '胜者' in name:
                # 提取组号
                import re
                # 匹配任何字母或数字
                group_match = re.search(r'[A-Za-z0-9]', name)
                if group_match:
                    group = group_match.group()
                    return f'洲际附加赛{group}组胜者'
            # 处理沙特的不同格式
            elif '沙特' in name:
                return '沙特阿拉伯'
            return name

        # 初始化队伍统计数据
        team_stats = {}
        for team in teams:
            team_id, team_name, group_id = team
            # 标准化队伍名称
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

            # 标准化队伍名称
            normalized_team1 = normalize_team_name(team1)
            normalized_team2 = normalize_team_name(team2)

            # 获取当前比赛的group_id
            cursor.execute("SELECT id FROM groups WHERE group_name = ?", (group_name,))
            group_result = cursor.fetchone()
            current_group_id = group_result[0] if group_result else 1

            # 确保队伍1在team_stats中
            if normalized_team1 not in team_stats:
                # 尝试获取队伍的group_id，如果找不到则使用当前比赛的group_id
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
                # 尝试获取队伍的group_id，如果找不到则使用当前比赛的group_id
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
            # 先按积分降序，再按净胜球降序，再按进球数降序
            group_teams.sort(key=lambda x: (-x['points'], -x['goal_difference'], -x['goals_for']))

        # 获取小组名称
        cursor.execute("SELECT id, group_name FROM groups")
        groups = {id: name for id, name in cursor.fetchall()}

        # 组合小组名称和排名
        result = []
        for group_id, group_teams in grouped_stats.items():
            group_name = groups.get(group_id, f'Group {group_id}')
            # 如果指定了小组，则只返回该小组的排名
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
        print(f"Error in get_group_rankings: {e}")
        return []
    finally:
        db_pool.return_connection(conn)

# 初始化淘汰赛对阵表（32强）
def init_knockout_matchups():
    conn = db_pool.get_connection()
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
        print(f"Error in init_knockout_matchups: {e}")
        conn.rollback()
    finally:
        db_pool.return_connection(conn)

# 获取小组排名的队伍名称映射
def get_group_team_mapping():
    rankings = get_group_rankings()
    mapping = {}

    for group in rankings:
        group_name = group['group_name'].replace('组', '')
        for idx, team in enumerate(group['teams'], 1):
            mapping[f'{group_name}{idx}'] = team['team_name']

    # 处理小组第三的比较逻辑
    mapping.update(get_best_third_place_teams())

    return mapping

# 检查小组赛是否全部完成
def is_group_stage_completed():
    conn = db_pool.get_connection()
    try:
        cursor = conn.cursor()

        # 检查是否存在未完成的小组赛
        cursor.execute("SELECT COUNT(*) FROM matches WHERE stage = '小组赛' AND status != 'finished'")
        unfinished_count = cursor.fetchone()[0]

        return unfinished_count == 0
    except Error as e:
        print(f"Error in is_group_stage_completed: {e}")
        return False
    finally:
        db_pool.return_connection(conn)

# 获取成绩最好的小组第三
def get_best_third_place_teams():
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

    # 保留原有映射以保持兼容性
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

# 更新淘汰赛对阵表中的实际队伍
def update_knockout_teams():
    # 只有当小组赛全部完成时才更新淘汰赛队伍
    if not is_group_stage_completed():
        return

    conn = db_pool.get_connection()
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
        print(f"Error in update_knockout_teams: {e}")
        conn.rollback()
    finally:
        db_pool.return_connection(conn)

# 获取淘汰赛对阵数据（用于赛程图）
def get_knockout_bracket_data():
    conn = db_pool.get_connection()
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
        print(f"Error in get_knockout_bracket_data: {e}")
        return []
    finally:
        db_pool.return_connection(conn)

# 获取所有小组赛
def get_group_matches(group=None):
    conn = db_pool.get_connection()
    try:
        cursor = conn.cursor()

        if group:
            cursor.execute(
                "SELECT id, team1, team2, match_time, stage, group_name, status, score1, score2 FROM matches WHERE stage = '小组赛' AND group_name = ? ORDER BY match_time",
                (group + '组',)
            )
        else:
            cursor.execute(
                "SELECT id, team1, team2, match_time, stage, group_name, status, score1, score2 FROM matches WHERE stage = '小组赛' ORDER BY match_time"
            )
        matches = cursor.fetchall()

        # 获取每个比赛的最新赔率
        matches_with_odds = []
        for match in matches:
            match_id = match[0]
            cursor.execute(
                "SELECT win_odds, draw_odds, lose_odds, update_time FROM odds WHERE match_id = ? ORDER BY update_time DESC LIMIT 1",
                (match_id,)
            )
            odds = cursor.fetchone()
            matches_with_odds.append((match, odds))

        return matches_with_odds
    except Error as e:
        print(f"Error in get_group_matches: {e}")
        return []
    finally:
        db_pool.return_connection(conn)

# 获取所有淘汰赛
def get_knockout_matches():
    # 检查小组赛是否完成
    if not is_group_stage_completed():
        return []

    conn = db_pool.get_connection()
    try:
        cursor = conn.cursor()

        # 联合查询获取淘汰赛比赛及其对应的轮次
        cursor.execute(
            """
            SELECT m.id, m.team1, m.team2, m.match_time, m.stage, m.status, m.score1, m.score2, km.round_name
            FROM matches m
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
        )
        matches = cursor.fetchall()

        # 获取每个比赛的最新赔率
        matches_with_odds = []
        for match in matches:
            match_id = match[0]
            cursor.execute(
                "SELECT win_odds, draw_odds, lose_odds, update_time FROM odds WHERE match_id = ? ORDER BY update_time DESC LIMIT 1",
                (match_id,)
            )
            odds = cursor.fetchone()
            matches_with_odds.append((match, odds))

        return matches_with_odds
    except Error as e:
        print(f"Error in get_knockout_matches: {e}")
        return []
    finally:
        db_pool.return_connection(conn)

# 获取所有小组赛信息（用于管理页面）
def get_all_group_matches():
    conn = db_pool.get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, team1, team2, match_time, stage, group_name, status, score1, score2 FROM matches WHERE stage = '小组赛' ORDER BY group_name, match_time"
        )
        matches = cursor.fetchall()

        return matches
    except Error as e:
        print(f"Error in get_all_group_matches: {e}")
        return []
    finally:
        db_pool.return_connection(conn)

# 添加小组赛信息
def add_group_match(team1, team2, match_time, group_name):
    conn = db_pool.get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO matches (team1, team2, match_time, stage, group_name) VALUES (?, ?, ?, ?, ?)",
            (team1, team2, match_time, '小组赛', group_name)
        )

        conn.commit()
    except Error as e:
        print(f"Error in add_group_match: {e}")
        conn.rollback()
    finally:
        db_pool.return_connection(conn)

# 获取所有小组
def get_all_groups():
    conn = db_pool.get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT id, group_name FROM groups ORDER BY id")
        groups = cursor.fetchall()

        return groups
    except Error as e:
        print(f"Error in get_all_groups: {e}")
        return []
    finally:
        db_pool.return_connection(conn)

# 获取小组的所有队伍
def get_teams_by_group(group_id):
    conn = db_pool.get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("SELECT id, team_name FROM teams WHERE group_id = ? ORDER BY id", (group_id,))
        teams = cursor.fetchall()

        return teams
    except Error as e:
        print(f"Error in get_teams_by_group: {e}")
        return []
    finally:
        db_pool.return_connection(conn)

# 添加队伍到小组
def add_team_to_group(team_name, group_id):
    conn = db_pool.get_connection()
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
        print(f"Error in add_team_to_group: {e}")
        conn.rollback()
        return False
    finally:
        db_pool.return_connection(conn)

# 删除队伍
def delete_team(team_id):
    conn = db_pool.get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute("DELETE FROM teams WHERE id = ?", (team_id,))

        conn.commit()
    except Error as e:
        print(f"Error in delete_team: {e}")
        conn.rollback()
    finally:
        db_pool.return_connection(conn)

# 为小组生成比赛
def generate_group_matches(group_id, group_name):
    conn = db_pool.get_connection()
    try:
        cursor = conn.cursor()

        # 获取小组的所有队伍
        cursor.execute("SELECT team_name FROM teams WHERE group_id = ?", (group_id,))
        teams = [row[0] for row in cursor.fetchall()]

        # 生成两两队伍的比赛
        import itertools
        matches = list(itertools.combinations(teams, 2))

        # 插入比赛到数据库
        for team1, team2 in matches:
            # 默认比赛时间为当前时间（实际应用中应该由用户输入）
            match_time = datetime.now().strftime("%Y-%m-%d %H:%M")
            cursor.execute(
                "INSERT INTO matches (team1, team2, match_time, stage, group_name) VALUES (?, ?, ?, ?, ?)",
                (team1, team2, match_time, '小组赛', group_name)
            )

        conn.commit()
    except Error as e:
        print(f"Error in generate_group_matches: {e}")
        conn.rollback()
    finally:
        db_pool.return_connection(conn)

# 获取单个比赛信息
def get_match_by_id(match_id):
    conn = db_pool.get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, team1, team2, match_time, stage, group_name, status, score1, score2 FROM matches WHERE id = ?",
            (match_id,)
        )
        match = cursor.fetchone()

        return match
    except Error as e:
        print(f"Error in get_match_by_id: {e}")
        return None
    finally:
        db_pool.return_connection(conn)

# 更新比赛信息
def update_match_info(match_id, team1, team2, match_time, group_name, status, score1, score2):
    conn = db_pool.get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE matches SET team1 = ?, team2 = ?, match_time = ?, group_name = ?, status = ?, score1 = ?, score2 = ? WHERE id = ?",
            (team1, team2, match_time, group_name, status, score1, score2, match_id)
        )

        conn.commit()
    except Error as e:
        print(f"Error in update_match_info: {e}")
        conn.rollback()
    finally:
        db_pool.return_connection(conn)

# 更新比赛结果
def update_match_result(match_id, score1, score2):
    conn = db_pool.get_connection()
    try:
        cursor = conn.cursor()

        cursor.execute(
            "UPDATE matches SET status = 'finished', score1 = ?, score2 = ? WHERE id = ?",
            (score1, score2, match_id)
        )

        conn.commit()
    except Error as e:
        print(f"Error in update_match_result: {e}")
        conn.rollback()
    finally:
        db_pool.return_connection(conn)

# ============================================================
# 定时任务
# ============================================================
def scheduled_task():
    while True:
        crawler.update_odds()
        time.sleep(3600)  # 每小时执行一次

# 启动定时任务线程
task_thread = threading.Thread(target=scheduled_task)
task_thread.daemon = True
task_thread.start()

# ============================================================
# 原有模板路由（保持不变，向后兼容）
# ============================================================
@app.route('/')
def index():
    # 从GET请求获取日期参数
    date = request.args.get('date')
    if not date:
        # 如果没有指定日期，使用今天
        date = datetime.now().strftime("%Y-%m-%d")

    # 获取指定日期的比赛
    day_matches = get_matches_by_date(date)

    # 如果当日没有比赛，跳转到最近有比赛的日期
    if not day_matches and date == datetime.now().strftime("%Y-%m-%d"):
        next_date = get_next_match_date()
        if next_date != date:
            return redirect(f'/?date={next_date}')

    # 获取往后的赛程（从明天开始，显示7天）
    tomorrow = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    upcoming_matches = get_upcoming_matches(tomorrow, 7)

    # 按日期分组
    grouped_upcoming = group_matches_by_date(upcoming_matches)

    return render_template('index.html', date=date, day_matches=day_matches, grouped_upcoming=grouped_upcoming, flag_map=flag_map)

@app.route('/<date>')
def index_with_date(date):
    # 获取指定日期的比赛
    day_matches = get_matches_by_date(date)

    # 如果当日没有比赛，跳转到最近有比赛的日期
    if not day_matches and date == datetime.now().strftime("%Y-%m-%d"):
        next_date = get_next_match_date()
        if next_date != date:
            return redirect(f'/?date={next_date}')

    # 获取往后的赛程（从明天开始，显示7天）
    tomorrow = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    upcoming_matches = get_upcoming_matches(tomorrow, 7)

    # 按日期分组
    grouped_upcoming = group_matches_by_date(upcoming_matches)

    return render_template('index.html', date=date, day_matches=day_matches, grouped_upcoming=grouped_upcoming, flag_map=flag_map)

@app.route('/group_stage')
@app.route('/group_stage/<group>')
def group_stage(group=None):
    matches = get_group_matches(group)
    return render_template('group_stage.html', matches=matches, current_group=group, flag_map=flag_map)

@app.route('/knockout')
def knockout():
    matches = get_knockout_matches()
    return render_template('knockout.html', matches=matches, flag_map=flag_map)

@app.route('/knockout/bracket')
def knockout_bracket():
    bracket_data = get_knockout_bracket_data()
    return render_template('knockout_bracket.html', bracket_data=bracket_data, flag_map=flag_map)

@app.route('/rankings')
@app.route('/rankings/<group>')
def rankings(group=None):
    group_rankings = get_group_rankings(group)
    return render_template('rankings.html', group_rankings=group_rankings, flag_map=flag_map, current_group=group)

@app.route('/update_result', methods=['POST'])
def update_result():
    match_id = request.form['match_id']
    score1 = request.form['score1']
    score2 = request.form['score2']
    update_match_result(match_id, score1, score2)
    # 返回 JSON 响应而不是重定向
    return {'status': 'success', 'message': '比赛结果已更新'}

@app.route('/admin')
def admin():
    return redirect(url_for('group_team_management'))

@app.route('/admin/group_team_management')
def group_team_management():
    groups = get_all_groups()

    # 获取每个小组的队伍
    group_teams = {}
    for group in groups:
        group_id = group[0]
        group_teams[group_id] = get_teams_by_group(group_id)

    return render_template('group_team_management.html', groups=groups, group_teams=group_teams)

@app.route('/admin/match_management')
def match_management():
    matches = get_all_group_matches()
    return render_template('match_management.html', matches=matches)

@app.route('/admin/match_generation')
def match_generation():
    groups = get_all_groups()

    # 获取每个小组的队伍
    group_teams = {}
    for group in groups:
        group_id = group[0]
        group_teams[group_id] = get_teams_by_group(group_id)

    return render_template('match_generation.html', groups=groups, group_teams=group_teams)

@app.route('/admin/add_team', methods=['POST'])
def add_team():
    team_name = request.form['team_name']
    group_id = request.form['group_id']
    success = add_team_to_group(team_name, group_id)
    # 可以在这里添加成功或失败的提示，这里简单重定向
    return redirect(url_for('group_team_management'))

@app.route('/admin/delete_team', methods=['POST'])
def delete_team_route():
    team_id = request.form['team_id']
    delete_team(team_id)
    return redirect(url_for('group_team_management'))

@app.route('/admin/generate_matches', methods=['POST'])
def generate_matches():
    group_id = request.form['generate_group_id']

    # 获取小组名称
    conn = sqlite3.connect('worldcup.db')
    cursor = conn.cursor()
    cursor.execute("SELECT group_name FROM groups WHERE id = ?", (group_id,))
    group_name = cursor.fetchone()[0]
    conn.close()

    generate_group_matches(group_id, group_name)
    return redirect(url_for('admin'))

@app.route('/admin/add_group_match', methods=['POST'])
def add_group_match_route():
    team1 = request.form['team1']
    team2 = request.form['team2']
    match_time = request.form['match_time']
    group_name = request.form['group_name']
    add_group_match(team1, team2, match_time, group_name)
    return redirect(url_for('admin'))

@app.route('/admin/edit_match/<match_id>')
def edit_match(match_id):
    match = get_match_by_id(match_id)
    return render_template('edit_match.html', match=match)

@app.route('/admin/update_match/<match_id>', methods=['POST'])
def update_match(match_id):
    team1 = request.form['team1']
    team2 = request.form['team2']
    match_time = request.form['match_time']
    group_name = request.form['group_name']
    status = request.form['status']
    score1 = request.form['score1'] if request.form['score1'] else None
    score2 = request.form['score2'] if request.form['score2'] else None
    update_match_info(match_id, team1, team2, match_time, group_name, status, score1, score2)
    return redirect(url_for('admin'))


# ============================================================
# JSON API v1 路由
# ============================================================

# --- 比赛相关 API ---

@app.route('/api/v1/matches')
def api_matches():
    """获取比赛列表。支持 ?date=YYYY-MM-DD 查询参数。"""
    try:
        date = request.args.get('date')
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        # 获取指定日期的比赛
        day_matches_raw = get_matches_by_date(date)
        day_matches = [serialize_match(m, o) for m, o in day_matches_raw]

        # 获取未来赛程
        tomorrow = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        upcoming_raw = get_upcoming_matches(tomorrow, 7)
        upcoming_matches = [serialize_match(m, o) for m, o in upcoming_raw]

        # 按日期分组
        grouped_raw = group_matches_by_date(upcoming_raw)
        grouped_upcoming = {}
        for g_date, items in grouped_raw.items():
            grouped_upcoming[g_date] = [serialize_match(m, o) for m, o in items]

        return jsonify({
            'day_matches': day_matches,
            'upcoming_matches': upcoming_matches,
            'grouped_upcoming': grouped_upcoming
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/matches/<int:match_id>/result', methods=['POST'])
def api_update_result(match_id):
    """更新比赛结果。支持 JSON body 和 form data。"""
    try:
        # 同时支持 JSON body 和 form data（Vue 前端发送 JSON）
        if request.is_json:
            data = request.get_json()
            score1 = data.get('score1')
            score2 = data.get('score2')
        else:
            score1 = request.form.get('score1')
            score2 = request.form.get('score2')

        if score1 is None or score2 is None:
            return jsonify({'status': 'error', 'message': '缺少 score1 或 score2 参数'}), 400

        update_match_result(match_id, score1, score2)
        return jsonify({'status': 'success', 'message': '比赛结果已更新'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# --- 小组赛相关 API ---

@app.route('/api/v1/group_stage')
def api_group_stage():
    """获取小组赛比赛。支持 ?group=X 查询参数。"""
    try:
        group = request.args.get('group')
        matches_raw = get_group_matches(group)
        matches = [serialize_match(m, o) for m, o in matches_raw]
        current_group = group if group else ''
        return jsonify({
            'matches': matches,
            'current_group': current_group
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# --- 淘汰赛相关 API ---

@app.route('/api/v1/knockout')
def api_knockout():
    """获取淘汰赛比赛列表。"""
    try:
        matches_raw = get_knockout_matches()
        matches = [serialize_match(m, o) for m, o in matches_raw]
        return jsonify({
            'matches': matches
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/knockout/bracket')
def api_knockout_bracket():
    """获取淘汰赛对阵图数据。"""
    try:
        bracket_data = get_knockout_bracket_data()
        return jsonify({
            'bracket_data': bracket_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# --- 排名相关 API ---

@app.route('/api/v1/rankings')
def api_rankings():
    """获取小组排名。支持 ?group=X 查询参数。"""
    try:
        group = request.args.get('group')
        rankings = get_group_rankings(group)
        current_group = group if group else ''
        return jsonify({
            'rankings': rankings,
            'current_group': current_group
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# --- 管理后台 API ---

@app.route('/api/v1/admin/groups')
def api_admin_groups():
    """获取所有小组及其队伍。"""
    try:
        groups = get_all_groups()
        groups_list = [{'id': g[0], 'group_name': g[1]} for g in groups]

        group_teams = {}
        for group in groups:
            group_id = group[0]
            teams = get_teams_by_group(group_id)
            group_teams[group_id] = [{'id': t[0], 'team_name': t[1]} for t in teams]

        return jsonify({
            'groups': groups_list,
            'group_teams': group_teams
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/admin/teams', methods=['POST'])
def api_admin_add_team():
    """添加队伍到小组。"""
    try:
        if request.is_json:
            data = request.get_json()
            team_name = data.get('team_name')
            group_id = data.get('group_id')
        else:
            team_name = request.form.get('team_name')
            group_id = request.form.get('group_id')

        if not team_name or not group_id:
            return jsonify({'status': 'error', 'message': '缺少 team_name 或 group_id 参数'}), 400

        success = add_team_to_group(team_name, group_id)
        if success:
            return jsonify({'status': 'success', 'message': '队伍添加成功'})
        else:
            return jsonify({'status': 'error', 'message': '该小组已有4支队伍，无法继续添加'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/v1/admin/teams/<int:team_id>', methods=['DELETE'])
def api_admin_delete_team(team_id):
    """删除队伍。"""
    try:
        delete_team(team_id)
        return jsonify({'status': 'success', 'message': '队伍已删除'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/v1/admin/matches/generate', methods=['POST'])
def api_admin_generate_matches():
    """为指定小组生成比赛。"""
    try:
        if request.is_json:
            data = request.get_json()
            group_id = data.get('group_id')
        else:
            group_id = request.form.get('group_id')

        if not group_id:
            return jsonify({'status': 'error', 'message': '缺少 group_id 参数'}), 400

        # 获取小组名称
        conn = sqlite3.connect('worldcup.db')
        cursor = conn.cursor()
        cursor.execute("SELECT group_name FROM groups WHERE id = ?", (group_id,))
        result = cursor.fetchone()
        conn.close()

        if not result:
            return jsonify({'status': 'error', 'message': '小组不存在'}), 404

        group_name = result[0]
        generate_group_matches(group_id, group_name)
        return jsonify({'status': 'success', 'message': '比赛生成成功'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/v1/admin/group_matches', methods=['POST'])
def api_admin_add_group_match():
    """手动添加小组赛。"""
    try:
        if request.is_json:
            data = request.get_json()
            team1 = data.get('team1')
            team2 = data.get('team2')
            match_time = data.get('match_time')
            group_name = data.get('group_name')
        else:
            team1 = request.form.get('team1')
            team2 = request.form.get('team2')
            match_time = request.form.get('match_time')
            group_name = request.form.get('group_name')

        if not all([team1, team2, match_time, group_name]):
            return jsonify({'status': 'error', 'message': '缺少必要参数 (team1, team2, match_time, group_name)'}), 400

        add_group_match(team1, team2, match_time, group_name)
        return jsonify({'status': 'success', 'message': '小组赛添加成功'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@app.route('/api/v1/admin/matches')
def api_admin_matches():
    """获取所有小组赛比赛（管理用）。"""
    try:
        matches = get_all_group_matches()
        matches_list = []
        for m in matches:
            matches_list.append({
                'id': m[0],
                'team1': m[1],
                'team2': m[2],
                'match_time': m[3],
                'stage': m[4],
                'group_name': m[5],
                'status': m[6],
                'score1': m[7],
                'score2': m[8]
            })
        return jsonify({
            'matches': matches_list
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/admin/matches/<int:match_id>')
def api_admin_get_match(match_id):
    """获取单个比赛详情。"""
    try:
        match = get_match_by_id(match_id)
        if match is None:
            return jsonify({'error': '比赛不存在'}), 404

        match_dict = {
            'id': match[0],
            'team1': match[1],
            'team2': match[2],
            'match_time': match[3],
            'stage': match[4],
            'group_name': match[5],
            'status': match[6],
            'score1': match[7],
            'score2': match[8]
        }
        return jsonify({
            'match': match_dict
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/v1/admin/matches/<int:match_id>', methods=['PUT'])
def api_admin_update_match(match_id):
    """更新比赛信息。"""
    try:
        if request.is_json:
            data = request.get_json()
            team1 = data.get('team1')
            team2 = data.get('team2')
            match_time = data.get('match_time')
            group_name = data.get('group_name')
            status = data.get('status')
            score1 = data.get('score1')
            score2 = data.get('score2')
        else:
            team1 = request.form.get('team1')
            team2 = request.form.get('team2')
            match_time = request.form.get('match_time')
            group_name = request.form.get('group_name')
            status = request.form.get('status')
            score1 = request.form.get('score1')
            score2 = request.form.get('score2')

        if not all([team1, team2, match_time, group_name, status]):
            return jsonify({'status': 'error', 'message': '缺少必要参数'}), 400

        update_match_info(match_id, team1, team2, match_time, group_name, status, score1, score2)
        return jsonify({'status': 'success', 'message': '比赛信息已更新'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# ============================================================
# 启动入口
# ============================================================
if __name__ == '__main__':
    init_db()
    init_knockout_matchups()
    update_knockout_teams()
    crawler.update_odds()
    app.run(debug=True, host='0.0.0.0', port=5004)
