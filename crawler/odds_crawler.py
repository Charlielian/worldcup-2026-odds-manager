import requests
import sqlite3
from datetime import datetime
import time
import random

DATABASE = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    return conn

def crawl_odds():
    """
    爬取足彩赔率数据（示例：使用合法体育数据网站，实际需替换为目标网址）
    注意：需遵守目标网站的robots.txt协议，避免非法爬取
    """
    # 合法数据源推荐：需选择有公开API/允许爬取的体育数据网站
    # 以下为示例框架，需根据实际网站结构调整
    target_url = "https://www.example-sports-data.com/worldcup2026/odds"  # 替换为实际网址
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Referer': 'https://www.example-sports-data.com/',
        'Accept-Language': 'zh-CN,zh;q=0.9'
    }
    
    try:
        # 随机延迟避免反爬
        time.sleep(random.uniform(1, 3))
        response = requests.get(target_url, headers=headers, timeout=10)
        response.raise_for_status()  # 抛出HTTP错误
        
        # 解析数据（示例：需根据实际网页结构调整，推荐使用BeautifulSoup）
        # from bs4 import BeautifulSoup
        # soup = BeautifulSoup(response.text, 'html.parser')
        # 以下为模拟解析结果，实际需替换为真实解析逻辑
        odds_data = [
            {'match_id': 1, 'home_odds': 2.18, 'away_odds': 3.75, 'draw_odds': 3.18},
            {'match_id': 2, 'home_odds': 2.32, 'away_odds': 3.48, 'draw_odds': 2.98}
        ]
        
        # 写入数据库
        conn = get_db_connection()
        for data in odds_data:
            conn.execute('INSERT INTO odds (match_id, home_odds, away_odds, draw_odds) VALUES (?, ?, ?, ?)',
                         (data['match_id'], data['home_odds'], data['away_odds'], data['draw_odds']))
        conn.commit()
        conn.close()
        print(f"[{datetime.now()}] 赔率数据爬取成功")
        
    except Exception as e:
        print(f"[{datetime.now()}] 赔率数据爬取失败：{str(e)}")

if __name__ == '__main__':
    # 测试爬虫
    crawl_odds()