import requests
from bs4 import BeautifulSoup
import sqlite3
import time
from datetime import datetime

def get_odds_from_source():
    # 模拟获取赔率数据，实际项目中需要根据具体网站结构进行爬取
    # 这里使用示例数据
    return [
        {"team1": "巴西", "team2": "阿根廷", "win_odds": 1.8, "draw_odds": 3.5, "lose_odds": 4.0},
        {"team1": "法国", "team2": "德国", "win_odds": 2.0, "draw_odds": 3.2, "lose_odds": 3.8},
        {"team1": "英格兰", "team2": "西班牙", "win_odds": 2.2, "draw_odds": 3.0, "lose_odds": 3.5}
    ]

def update_odds():
    conn = sqlite3.connect('worldcup.db')
    cursor = conn.cursor()
    
    # 获取所有未结束的比赛
    cursor.execute("SELECT id, team1, team2 FROM matches WHERE status = 'upcoming'")
    matches = cursor.fetchall()
    
    # 获取赔率数据
    odds_data = get_odds_from_source()
    
    # 更新赔率
    for match in matches:
        match_id, team1, team2 = match
        
        # 查找对应比赛的赔率
        for data in odds_data:
            if data["team1"] == team1 and data["team2"] == team2:
                # 插入新的赔率记录
                update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cursor.execute(
                    "INSERT INTO odds (match_id, win_odds, draw_odds, lose_odds, update_time) VALUES (?, ?, ?, ?, ?)",
                    (match_id, data["win_odds"], data["draw_odds"], data["lose_odds"], update_time)
                )
                break
    
    conn.commit()
    conn.close()
    print(f"赔率更新完成: {datetime.now()}")

if __name__ == "__main__":
    update_odds()