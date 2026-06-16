#!/usr/bin/env python3
"""按用户最新提供的官方淘汰赛赛程，刷新 knockout_matchups + matches。

约定：
- 保留现有 match_number (1-32) 与 position 等列，叠加新增列：
    - bracket_code : 业务编号，如 'R16-1', 'R8-91', 'QF-99', 'SF-1', '3RD', 'FNL'
    - allowed_third_groups : 槽位为「待定第三名」时，合法的小组枚举（逗号分隔）
- slot 里把"待定小组第三名"统一存为 'TBD_3RD'，allowed_third_groups 写明可选组
- matches 表的 32 场淘汰赛：修正 match_time、stage（季军赛 -> 三四名决赛）、
  team1/team2 写为与 slot 同义的占位符，让前端/移动端在小组赛结束前显示
  晋级身份（A 组第 1 / I 组第 1 / TBD_3RD ...）。

注意：
- 本脚本幂等：每次执行都先 DELETE 旧数据再 INSERT。可重复运行。
- 不动小组赛和赔率（除了清理指向旧 id 的孤立赔率）。
"""

import sqlite3
import sys
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "worldcup.db"

# 单一数据源
from backend.services.knockout_schema import KNOCKOUT  # noqa: E402


def ensure_schema(cursor):
    """幂等式地加上新列。"""
    cursor.execute("PRAGMA table_info(knockout_matchups)")
    cols = {row[1] for row in cursor.fetchall()}
    if 'bracket_code' not in cols:
        cursor.execute("ALTER TABLE knockout_matchups ADD COLUMN bracket_code TEXT")
    if 'allowed_third_groups' not in cols:
        cursor.execute("ALTER TABLE knockout_matchups ADD COLUMN allowed_third_groups TEXT")


def migrate():
    if len(KNOCKOUT) != 32:
        print(f"警告：KNOCKOUT 条目 = {len(KNOCKOUT)}，应为 32", file=sys.stderr)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    ensure_schema(cursor)

    # 清空两个表的淘汰赛数据，按新赛程重建
    cursor.execute("DELETE FROM knockout_matchups")
    cursor.execute(
        "DELETE FROM matches WHERE stage IN "
        "('1/16决赛','1/8决赛','1/4决赛','半决赛','季军赛','三四名决赛','决赛','淘汰赛')"
    )

    # 清理指向被删 id 的孤立赔率
    cursor.execute(
        "SELECT COUNT(*) FROM odds o WHERE NOT EXISTS (SELECT 1 FROM matches m WHERE m.id = o.match_id)"
    )
    orphan_odds = cursor.fetchone()[0]
    if orphan_odds:
        cursor.execute("DELETE FROM odds WHERE match_id NOT IN (SELECT id FROM matches)")

    # 写入 knockout_matchups
    insert_ko = """
        INSERT INTO knockout_matchups (
            match_number, round_name, position, slot1_team_group, slot2_team_group,
            venue, match_time, bracket_code, allowed_third_groups
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    for (mn, rnd, pos, code, s1, s2, a1, a2, mt, stage, t1, t2, venue) in KNOCKOUT:
        allowed = None
        if a1 or a2:
            allowed = ";".join(filter(None, [a1 or "", a2 or ""]))
        cursor.execute(insert_ko, (mn, rnd, pos, s1, s2, venue, mt, code, allowed))

    # 写入 matches，id 从 280 起保持与旧版兼容
    cursor.execute("SELECT COALESCE(MIN(id), 280) FROM matches WHERE id >= 280")
    existing_min = cursor.fetchone()[0]
    next_id = 280 if existing_min is None or existing_min > 280 else existing_min

    insert_match = """
        INSERT INTO matches (id, team1, team2, match_time, stage, status, group_name)
        VALUES (?, ?, ?, ?, ?, 'upcoming', NULL)
    """
    new_match_ids = []
    for (mn, rnd, pos, code, s1, s2, a1, a2, mt, stage, t1, t2, venue) in KNOCKOUT:
        cursor.execute(insert_match, (next_id, t1, t2, mt, stage))
        new_match_ids.append((next_id, mn, stage, mt))
        next_id += 1

    conn.commit()

    print(f"=== knockout_matchups 写入 {len(KNOCKOUT)} 条 ===")
    print(f"=== matches 写入 {len(KNOCKOUT)} 条，id 范围 {new_match_ids[0][0]} - {new_match_ids[-1][0]} ===")
    if orphan_odds:
        print(f"已清理 {orphan_odds} 条孤立赔率（指向被替换的旧比赛 id）")

    cursor.execute("SELECT COUNT(*) FROM knockout_matchups")
    print(f"knockout_matchups 现有 {cursor.fetchone()[0]} 条")
    cursor.execute(
        "SELECT COUNT(*) FROM matches WHERE stage IN ('1/16决赛','1/8决赛','1/4决赛','半决赛','三四名决赛','决赛')"
    )
    print(f"matches 淘汰赛现有 {cursor.fetchone()[0]} 条")
    cursor.execute("SELECT COUNT(*) FROM matches WHERE stage = '季军赛'")
    bad = cursor.fetchone()[0]
    if bad:
        print(f"!! 警告：仍有 {bad} 条 stage='季军赛' 的旧记录", file=sys.stderr)

    conn.close()


if __name__ == "__main__":
    migrate()
