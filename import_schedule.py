import sqlite3
from datetime import datetime

# 连接数据库
conn = sqlite3.connect('worldcup.db')
cursor = conn.cursor()

# 清空现有的小组赛数据
cursor.execute("DELETE FROM matches WHERE stage = '小组赛'")

# 赛程数据
schedule_data = """
A组 
 墨西哥VS南非 6月12日03:00 
 韩国VS欧洲区附加赛路径D胜者 6月12日10:00 
 欧洲区附加赛路径D胜者VS南非 6月19日00:00 
 墨西哥VS韩国 6月19日09:00 
 欧洲区附加赛路径D胜者VS墨西哥 6月25日09:00 
 南非VS韩国 6月25日09:00 
B组 
 加拿大VS欧洲区附加赛路径A胜者 6月13日03:00 
 卡塔尔VS瑞士 6月14日03:00 
 瑞士VS欧洲区附加赛路径A胜者 6月19日03:00 
 加拿大VS卡塔尔 6月19日06:00 
 瑞士VS加拿大 6月25日03:00 
 欧洲区附加赛路径A胜者VS卡塔尔 6月25日03:00 
C组 
 巴西VS摩洛哥 6月14日06:00 
 海地VS苏格兰 6月14日09:00 
 苏格兰VS摩洛哥 6月20日06:00 
 巴西VS海地 6月20日09:00 
 苏格兰VS巴西 6月25日06:00 
 摩洛哥VS海地 6月25日06:00 
D组 
 美国VS巴拉圭 6月13日09:00 
 澳大利亚VS欧洲区附加赛路径C胜者 6月14日12:00 
 欧洲区附加赛路径C胜者VS巴拉圭 6月20日12:00 
 美国VS澳大利亚 6月20日03:00 
 欧洲区附加赛路径C胜者VS美国 6月26日10:00 
 巴拉圭VS澳大利亚 6月26日10:00 
E组 
 德国VS库拉索 6月15日01:00 
 科特迪瓦VS厄瓜多尔 6月15日07:00 
 德国VS科特迪瓦 6月21日04:00 
 厄瓜多尔VS库拉索 6月21日08:00 
 厄瓜多尔VS德国 6月26日04:00 
 库拉索VS科特迪瓦 6月26日04:00 
F组 
 荷兰VS日本 6月15日04:00 
 欧洲区附加赛路径B胜者VS突尼斯 6月15日10:00 
 荷兰VS欧洲区附加赛路径B胜者6月21日01:00 
 突尼斯VS日本 6月20日12:00 
 日本VS欧洲区附加赛路径B胜者 6月26日07:00 
 突尼斯VS荷兰 6月26日07:00 
G组 
 伊朗VS新西兰 6月16日09:00 
 比利时VS埃及 6月16日03:00 
 比利时VS伊朗 6月22日03:00 
 新西兰VS埃及 6月22日09:00 
 埃及VS伊朗 6月27日11:00 
 新西兰VS比利时 6月27日11:00 
H组 
 西班牙VS佛得角 6月16日00:00 
 沙特VS乌拉圭 6月16日06:00 
 西班牙VS沙特 6月22日00:00 
 乌拉圭VS佛得角 6月22日06:00 
 佛得角VS沙特 6月27日08:00 
 乌拉圭VS西班牙 6月27日08:00 
I组 
 法国VS塞内加尔 6月16日03:00 
 洲际附加赛路径2胜者VS挪威 6月16日06:00 
 法国VS洲际附加赛路径2胜者 6月23日05:00 
 挪威VS塞内加尔 6月23日08:00 
 挪威VS法国 6月27日03:00 
 塞内加尔VS洲际附加赛路径2胜者 6月27日03:00 
J组 
 阿根廷VS阿尔及利亚 6月17日09:00 
 奥地利VS约旦 6月17日12:00 
 阿根廷VS奥地利 6月23日01:00 
 约旦VS阿尔及利亚 6月23日11:00 
 阿尔及利亚VS奥地利 6月28日10:00 
 约旦VS阿根廷 6月28日10:00 
K组 
 葡萄牙VS洲际附加赛路径1胜者 6月18日01:00 
 乌兹别克斯坦VS哥伦比亚 6月18日10:00 
 葡萄牙VS乌兹别克斯坦 6月24日01:00 
 哥伦比亚VS洲际附加赛路径1胜者 6月24日10:00 
 哥伦比亚VS葡萄牙 6月28日07:30 
 洲际附加赛路径1胜者VS乌兹别克斯坦 6月28日07:30 
L组 
 英格兰VS克罗地亚 6月18日04:00 
 加纳VS巴拿马 6月18日07:00 
 英格兰VS加纳 6月24日04:00 
 巴拿马VS克罗地亚 6月24日07:00 
 巴拿马VS英格兰 6月28日05:00 
 克罗地亚VS加纳 6月28日05:00
"""

# 解析赛程数据
lines = schedule_data.strip().split('\n')
current_group = None
matches = []

for line in lines:
    line = line.strip()
    if not line:
        continue
    
    # 检查是否是小组名称
    if line.endswith('组'):
        current_group = line
    else:
        # 解析比赛信息
        # 处理可能的格式问题
        if 'VS' not in line:
            continue
        
        # 提取队伍和时间
        parts = line.split('VS')
        if len(parts) != 2:
            continue
        
        team1 = parts[0].strip()
        # 提取team2和时间
        team2_time = parts[1].strip()
        # 找到最后一个空格的位置，分割队伍和时间
        last_space = team2_time.rfind(' ')
        if last_space == -1:
            continue
        
        team2 = team2_time[:last_space].strip()
        time_str = team2_time[last_space:].strip()
        
        # 处理时间格式
        # 格式：6月12日03:00
        if '月' in time_str and '日' in time_str:
            # 提取月、日、时间
            month_day = time_str.split('日')[0]
            month = month_day.split('月')[0]
            day = month_day.split('月')[1]
            time_part = time_str.split('日')[1]
            
            # 构造完整的日期时间字符串
            match_time = f"2026-{int(month):02d}-{int(day):02d} {time_part}"
            
            # 添加到比赛列表
            matches.append((team1, team2, match_time, '小组赛', current_group))

# 插入比赛数据
cursor.executemany(
    "INSERT INTO matches (team1, team2, match_time, stage, group_name) VALUES (?, ?, ?, ?, ?)",
    matches
)

# 提交更改并关闭连接
conn.commit()
conn.close()

print(f"成功导入 {len(matches)} 场小组赛赛程")