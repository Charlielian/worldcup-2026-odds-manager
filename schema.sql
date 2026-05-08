-- 小组表
CREATE TABLE IF NOT EXISTS groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_name TEXT NOT NULL UNIQUE
);

-- 队伍表
CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_name TEXT NOT NULL,
    group_id INTEGER NOT NULL,
    FOREIGN KEY (group_id) REFERENCES groups(id)
);

-- 比赛表
CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team1 TEXT NOT NULL,
    team2 TEXT NOT NULL,
    match_time TEXT NOT NULL,
    stage TEXT NOT NULL,  -- 小组赛/淘汰赛
    group_name TEXT,  -- 小组赛组别
    status TEXT DEFAULT 'upcoming',  -- upcoming/finished
    score1 INTEGER,
    score2 INTEGER
);

-- 赔率表
CREATE TABLE IF NOT EXISTS odds (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER NOT NULL,
    win_odds REAL NOT NULL,  -- 主队胜赔率
    draw_odds REAL NOT NULL,  -- 平局赔率
    lose_odds REAL NOT NULL,  -- 客队胜赔率
    update_time TEXT NOT NULL,
    source TEXT DEFAULT 'unknown',  -- 数据来源
    FOREIGN KEY (match_id) REFERENCES matches(id)
);

-- 淘汰赛对阵表（32强对阵）
CREATE TABLE IF NOT EXISTS knockout_matchups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_number INTEGER NOT NULL,  -- 场次编号 73-88 (16强), 89-96 (8强), 97-100 (4强), 101-102 (半决赛), 103 (三四名), 104 (决赛)
    round_name TEXT NOT NULL,  -- 1/16决赛, 1/8决赛, 1/4决赛, 半决赛, 三四名决赛, 决赛
    position TEXT NOT NULL,  -- 在赛程图中的位置，如 'left1', 'left2', 'center1' 等
    slot1_team_group TEXT,  -- 如 'A1', 'C3' 等，team1的预期位置
    slot2_team_group TEXT,  -- 如 'A2', 'B3' 等，team2的预期位置
    venue TEXT,  -- 比赛场地
    match_time TEXT  -- 比赛时间
);