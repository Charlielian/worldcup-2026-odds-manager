import sqlite3

# 连接数据库
conn = sqlite3.connect('worldcup.db')
cursor = conn.cursor()

# 检查小组信息
print("=== 小组信息 ===")
cursor.execute("SELECT * FROM groups ORDER BY id")
groups = cursor.fetchall()
for group in groups:
    print(f"ID: {group[0]}, 名称: {group[1]}")

# 检查队伍信息
print("\n=== 队伍信息 ===")
cursor.execute("SELECT COUNT(*) FROM teams")
total_teams = cursor.fetchone()[0]
print(f"队伍总数: {total_teams}")

# 检查每个小组的队伍
for group in groups:
    group_id, group_name = group
    cursor.execute("SELECT team_name FROM teams WHERE group_id = ?", (group_id,))
    teams = cursor.fetchall()
    print(f"\n{group_name}:")
    for team in teams:
        print(f"  - {team[0]}")

# 检查比赛信息
print("\n=== 比赛信息 ===")
cursor.execute("SELECT COUNT(*) FROM matches WHERE stage = '小组赛'")
total_matches = cursor.fetchone()[0]
print(f"小组赛总数: {total_matches}")

# 关闭连接
conn.close()
print("\n数据检查完成！")