from app import get_group_rankings

# 测试get_group_rankings函数
rankings = get_group_rankings()

# 打印每个组的队伍数量
for group in rankings:
    group_name = group['group_name']
    team_count = len(group['teams'])
    print(f"{group_name}: {team_count} teams")
    for team in group['teams']:
        print(f"  - {team['team_name']}")
    print()