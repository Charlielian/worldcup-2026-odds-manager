from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime, timedelta
import crawler
import threading
import time

# 国旗映射字典
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
    '苏格兰': '🏴󠁧󠁢󠁳󠁣󠁴󠁿',
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
    '英格兰': '🏴󠁧󠁢󠁥󠁮󠁧󠁿',
    '克罗地亚': '🇭🇷',
    '加纳': '🇬🇭',
    '巴拿马': '🇵🇦'
}

# 获取队伍的国旗
def get_flag(team_name):
    return flag_map.get(team_name, '')

app = Flask(__name__)

# 初始化数据库
def init_db():
    conn = sqlite3.connect('worldcup.db')
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
    conn.close()

# 获取指定日期的比赛
def get_matches_by_date(date):
    conn = sqlite3.connect('worldcup.db')
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, team1, team2, match_time, stage, status, score1, score2 FROM matches WHERE match_time LIKE ? ORDER BY match_time",
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
    
    conn.close()
    return matches_with_odds

# 获取往后的赛程（从指定日期开始的未来比赛）
def get_upcoming_matches(start_date, days=7):
    conn = sqlite3.connect('worldcup.db')
    cursor = conn.cursor()
    
    # 计算结束日期
    end_date = (datetime.strptime(start_date, "%Y-%m-%d") + timedelta(days=days)).strftime("%Y-%m-%d")
    
    cursor.execute(
        "SELECT id, team1, team2, match_time, stage, status, score1, score2 FROM matches WHERE match_time >= ? AND match_time < ? ORDER BY match_time",
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
    
    conn.close()
    return matches_with_odds

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
    conn = sqlite3.connect('worldcup.db')
    cursor = conn.cursor()
    
    # 获取所有未来的比赛，按日期排序
    today = datetime.now().strftime("%Y-%m-%d")
    cursor.execute(
        "SELECT DISTINCT DATE(match_time) as match_date FROM matches WHERE match_time >= ? ORDER BY match_date LIMIT 1",
        (today,)
    )
    result = cursor.fetchone()
    conn.close()
    
    if result:
        return result[0]
    return today

# 获取小组排名
def get_group_rankings():
    conn = sqlite3.connect('worldcup.db')
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
        team_stats[team_name] = {
            'team_id': team_id,
            'team_name': team_name,
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
        
        # 更新队伍1的统计数据
        if team1 in team_stats:
            team_stats[team1]['played'] += 1
            team_stats[team1]['goals_for'] += score1
            team_stats[team1]['goals_against'] += score2
            team_stats[team1]['goal_difference'] = team_stats[team1]['goals_for'] - team_stats[team1]['goals_against']
            
            if score1 > score2:
                team_stats[team1]['won'] += 1
                team_stats[team1]['points'] += 3
            elif score1 == score2:
                team_stats[team1]['drawn'] += 1
                team_stats[team1]['points'] += 1
            else:
                team_stats[team1]['lost'] += 1
        
        # 更新队伍2的统计数据
        if team2 in team_stats:
            team_stats[team2]['played'] += 1
            team_stats[team2]['goals_for'] += score2
            team_stats[team2]['goals_against'] += score1
            team_stats[team2]['goal_difference'] = team_stats[team2]['goals_for'] - team_stats[team2]['goals_against']
            
            if score2 > score1:
                team_stats[team2]['won'] += 1
                team_stats[team2]['points'] += 3
            elif score2 == score1:
                team_stats[team2]['drawn'] += 1
                team_stats[team2]['points'] += 1
            else:
                team_stats[team2]['lost'] += 1
    
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
    
    conn.close()
    
    # 组合小组名称和排名
    result = []
    for group_id, group_teams in grouped_stats.items():
        result.append({
            'group_id': group_id,
            'group_name': groups.get(group_id, f'Group {group_id}'),
            'teams': group_teams
        })
    
    # 按小组ID排序
        result.sort(key=lambda x: x['group_id'])
    
    return result

# 初始化淘汰赛对阵表（32强）
def init_knockout_matchups():
    conn = sqlite3.connect('worldcup.db')
    cursor = conn.cursor()
    
    # 检查是否已有数据
    cursor.execute("SELECT COUNT(*) FROM knockout_matchups")
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
    
    # 32强对阵数据
    knockout_data = [
        # 1/16决赛 (73-88)
        (73, '1/16决赛', 'left1_1', 'A1', 'C3/E3/F3/G3', '墨西哥城', '2026-06-29 03:00'),
        (74, '1/16决赛', 'left1_2', 'B1', 'A3/C3/D3/H3', '多伦多', '2026-06-29 10:00'),
        (75, '1/16决赛', 'left2_1', 'C1', 'A2', '亚特兰大', '2026-06-30 03:00'),
        (76, '1/16决赛', 'left2_2', 'D1', 'B2', '旧金山', '2026-06-30 10:00'),
        (77, '1/16决赛', 'left3_1', 'E1', 'D2', '西雅图', '2026-07-01 01:00'),
        (78, '1/16决赛', 'left3_2', 'F1', 'C2', '费城', '2026-07-01 08:00'),
        (79, '1/16决赛', 'left4_1', 'G1', 'F2', '休斯顿', '2026-07-02 01:00'),
        (80, '1/16决赛', 'left4_2', 'H1', 'E2', '洛杉矶', '2026-07-02 09:00'),
        (81, '1/16决赛', 'right1_1', 'I1', 'H2', '迈阿密', '2026-07-03 01:00'),
        (82, '1/16决赛', 'right1_2', 'J1', 'I2', '堪萨斯城', '2026-07-03 09:00'),
        (83, '1/16决赛', 'right2_1', 'K1', 'J2', '达拉斯', '2026-07-04 01:00'),
        (84, '1/16决赛', 'right2_2', 'L1', 'K2', '波士顿', '2026-07-04 08:00'),
        (85, '1/16决赛', 'right3_1', 'A2', 'B3/F3/G3/I3', '温哥华', '2026-07-04 01:00'),
        (86, '1/16决赛', 'right3_2', 'C2', 'D3/E3/H3/I3/L3', '纽约/新泽西', '2026-07-04 04:00'),
        (87, '1/16决赛', 'right4_1', 'E2', 'F3/G3/H3/I3/J3', '芝加哥', '2026-07-04 08:00'),
        (88, '1/16决赛', 'right4_2', 'G2', 'H3/I3/J3/K3/L3', '蒙特利尔', '2026-07-04 10:00'),
        # 1/8决赛 (89-96)
        (89, '1/8决赛', 'left_qf_1', '73胜者', '75胜者', '费城', '2026-07-05 01:00'),
        (90, '1/8决赛', 'left_qf_2', '74胜者', '77胜者', '休斯顿', '2026-07-05 04:00'),
        (91, '1/8决赛', 'right_qf_1', '76胜者', '78胜者', '洛杉矶', '2026-07-06 08:00'),
        (92, '1/8决赛', 'right_qf_2', '79胜者', '81胜者', '迈阿密', '2026-07-06 11:00'),
        (93, '1/8决赛', 'left_qf_3', '80胜者', '82胜者', '堪萨斯城', '2026-07-07 03:00'),
        (94, '1/8决赛', 'left_qf_4', '83胜者', '85胜者', '达拉斯', '2026-07-07 06:00'),
        (95, '1/8决赛', 'right_qf_3', '84胜者', '86胜者', '波士顿', '2026-07-08 00:00'),
        (96, '1/8决赛', 'right_qf_4', '87胜者', '88胜者', '亚特兰大', '2026-07-08 04:00'),
        # 半决赛 (97-98)
        (97, '半决赛', 'left_sf', '89胜者', '90胜者', '波士顿', '2026-07-10 04:00'),
        (98, '半决赛', 'right_sf', '93胜者', '94胜者', '洛杉矶', '2026-07-11 05:00'),
        (99, '半决赛', 'left_sf_2', '91胜者', '92胜者', '迈阿密', '2026-07-11 09:00'),
        (100, '半决赛', 'right_sf_2', '95胜者', '96胜者', '堪萨斯城', '2026-07-12 06:00'),
        # 三四名决赛
        (103, '三四名决赛', 'third_place', '97负者', '98负者', '迈阿密', '2026-07-19 05:00'),
        # 决赛
        (104, '决赛', 'final', '97胜者', '98胜者', '纽约/新泽西', '2026-07-20 08:00'),
    ]
    
    cursor.executemany(
        "INSERT INTO knockout_matchups (match_number, round_name, position, slot1_team_group, slot2_team_group, venue, match_time) VALUES (?, ?, ?, ?, ?, ?, ?)",
        knockout_data
    )
    
    conn.commit()
    conn.close()

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
    
    # 生成映射，例如 C3/E3/F3/G3 表示从C、E、F、G组中选择成绩最好的小组第三
    mapping = {}
    
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
    conn = sqlite3.connect('worldcup.db')
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
    conn.close()

# 获取淘汰赛对阵数据（用于赛程图）
def get_knockout_bracket_data():
    conn = sqlite3.connect('worldcup.db')
    cursor = conn.cursor()
    
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
    
    conn.close()
    return bracket_data

# 获取所有小组赛
def get_group_matches(group=None):
    conn = sqlite3.connect('worldcup.db')
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
    
    conn.close()
    return matches_with_odds

# 获取所有淘汰赛
def get_knockout_matches():
    conn = sqlite3.connect('worldcup.db')
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, team1, team2, match_time, stage, status, score1, score2 FROM matches WHERE stage = '淘汰赛' ORDER BY match_time"
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
    
    conn.close()
    return matches_with_odds

# 获取所有小组赛信息（用于管理页面）
def get_all_group_matches():
    conn = sqlite3.connect('worldcup.db')
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, team1, team2, match_time, stage, group_name, status, score1, score2 FROM matches WHERE stage = '小组赛' ORDER BY group_name, match_time"
    )
    matches = cursor.fetchall()
    
    conn.close()
    return matches

# 添加小组赛信息
def add_group_match(team1, team2, match_time, group_name):
    conn = sqlite3.connect('worldcup.db')
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO matches (team1, team2, match_time, stage, group_name) VALUES (?, ?, ?, ?, ?)",
        (team1, team2, match_time, '小组赛', group_name)
    )
    
    conn.commit()
    conn.close()

# 获取所有小组
def get_all_groups():
    conn = sqlite3.connect('worldcup.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, group_name FROM groups ORDER BY id")
    groups = cursor.fetchall()
    
    conn.close()
    return groups

# 获取小组的所有队伍
def get_teams_by_group(group_id):
    conn = sqlite3.connect('worldcup.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, team_name FROM teams WHERE group_id = ? ORDER BY id", (group_id,))
    teams = cursor.fetchall()
    
    conn.close()
    return teams

# 添加队伍到小组
def add_team_to_group(team_name, group_id):
    conn = sqlite3.connect('worldcup.db')
    cursor = conn.cursor()
    
    # 检查小组是否已经有4支队
    cursor.execute("SELECT COUNT(*) FROM teams WHERE group_id = ?", (group_id,))
    count = cursor.fetchone()[0]
    if count >= 4:
        conn.close()
        return False
    
    cursor.execute(
        "INSERT INTO teams (team_name, group_id) VALUES (?, ?)",
        (team_name, group_id)
    )
    
    conn.commit()
    conn.close()
    return True

# 删除队伍
def delete_team(team_id):
    conn = sqlite3.connect('worldcup.db')
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM teams WHERE id = ?", (team_id,))
    
    conn.commit()
    conn.close()

# 为小组生成比赛
def generate_group_matches(group_id, group_name):
    conn = sqlite3.connect('worldcup.db')
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
    conn.close()

# 获取单个比赛信息
def get_match_by_id(match_id):
    conn = sqlite3.connect('worldcup.db')
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, team1, team2, match_time, stage, group_name, status, score1, score2 FROM matches WHERE id = ?",
        (match_id,)
    )
    match = cursor.fetchone()
    
    conn.close()
    return match

# 更新比赛信息
def update_match_info(match_id, team1, team2, match_time, group_name, status, score1, score2):
    conn = sqlite3.connect('worldcup.db')
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE matches SET team1 = ?, team2 = ?, match_time = ?, group_name = ?, status = ?, score1 = ?, score2 = ? WHERE id = ?",
        (team1, team2, match_time, group_name, status, score1, score2, match_id)
    )
    
    conn.commit()
    conn.close()

# 更新比赛结果
def update_match_result(match_id, score1, score2):
    conn = sqlite3.connect('worldcup.db')
    cursor = conn.cursor()
    
    cursor.execute(
        "UPDATE matches SET status = 'finished', score1 = ?, score2 = ? WHERE id = ?",
        (score1, score2, match_id)
    )
    
    conn.commit()
    conn.close()

# 定时任务
def scheduled_task():
    while True:
        crawler.update_odds()
        time.sleep(3600)  # 每小时执行一次

# 启动定时任务线程
task_thread = threading.Thread(target=scheduled_task)
task_thread.daemon = True
task_thread.start()

# 路由
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
def rankings():
    group_rankings = get_group_rankings()
    return render_template('rankings.html', group_rankings=group_rankings, flag_map=flag_map)

@app.route('/update_result', methods=['POST'])
def update_result():
    match_id = request.form['match_id']
    score1 = request.form['score1']
    score2 = request.form['score2']
    update_match_result(match_id, score1, score2)
    return redirect(url_for('index'))

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

if __name__ == '__main__':
    init_db()
    init_knockout_matchups()
    update_knockout_teams()
    crawler.update_odds()
    app.run(debug=True, host='0.0.0.0', port=5001)