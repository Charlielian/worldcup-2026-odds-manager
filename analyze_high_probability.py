"""
世界杯高概率赢球分析脚本
筛选条件：
1. 3天内未开赛的比赛
2. 赢球概率 >= 90%（对应赔率 <= 1.11）
3. 最多显示5场比赛
"""

import sys
sys.path.insert(0, '/Users/charlie-macmini/Documents/python/世界杯')

from datetime import datetime, timedelta
from backend.services.sporttery_provider import SportteryProvider
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def calculate_implied_probability(odds):
    """根据赔率计算隐含概率"""
    if odds <= 0:
        return 0
    return (1 / odds) * 100


def show_all_matches(matches):
    """显示所有比赛及赔率分布"""
    output = []
    output.append("\n" + "=" * 70)
    output.append("📋 体彩在售比赛完整列表及赔率分析")
    output.append("=" * 70)

    now = datetime.now()
    today = now.date()

    # 显示所有比赛详情
    output.append(f"\n📅 所有比赛 ({len(matches)} 场):")
    output.append("-" * 70)

    all_matches_info = []
    for match in matches:
        match_date_str = match.get('match_date', '')
        match_time_str = match.get('match_time', '')

        match_datetime = None
        try:
            if match_date_str and match_time_str:
                # 支持 HH:MM 和 HH:MM:SS 格式
                time_format = '%H:%M:%S' if len(match_time_str.split(':')) == 3 else '%H:%M'
                match_datetime = datetime.strptime(f"{match_date_str} {match_time_str}", f"%Y-%m-%d {time_format}")
            elif match_date_str:
                match_datetime = datetime.strptime(match_date_str, "%Y-%m-%d")
        except ValueError:
            pass

        had = match.get('had')
        win_odds = 0
        draw_odds = 0
        lose_odds = 0
        win_prob = 0

        if had:
            win_odds = had.get('win', 0)
            draw_odds = had.get('draw', 0)
            lose_odds = had.get('lose', 0)
            if win_odds > 0:
                win_prob = calculate_implied_probability(win_odds)

        all_matches_info.append({
            'match': match,
            'datetime': match_datetime,
            'win_prob': win_prob,
            'win_odds': win_odds,
            'draw_odds': draw_odds,
            'lose_odds': lose_odds
        })

    # 按比赛时间排序
    all_matches_info.sort(key=lambda x: x['datetime'] if x['datetime'] else datetime(2099, 12, 31))

    for item in all_matches_info:
        match = item['match']
        dt = item['datetime']
        prob = item['win_prob']

        date_str = match.get('match_date', '未知')
        time_str = match.get('match_time', '')

        stars = "⭐" * int(prob / 20) if prob >= 60 else "○"
        time_info = ""
        if dt:
            match_date = dt.date()
            days_diff = (match_date - today).days
            if days_diff == 0:
                time_info = " [今天]"
            elif days_diff == 1:
                time_info = " [明天]"
            elif days_diff > 1:
                time_info = f" [距今 {days_diff} 天]"
            else:
                time_info = f" [已过 {-days_diff} 天]"

        output.append(f"  {date_str} {time_str} | {match.get('home_team', ''):>10} vs {match.get('away_team', ''):<10} | 胜率:{prob:5.1f}% | 赔率:{item['win_odds']:.2f} {stars}{time_info}")

    # 时间分布统计
    output.append(f"\n📊 比赛时间分布:")
    output.append("-" * 70)

    time_ranges = {
        '今天': 0,
        '明天': 0,
        '1-3天': 0,
        '4-7天': 0,
        '8-14天': 0,
        '15-30天': 0,
        '30天以上': 0
    }

    for item in all_matches_info:
        dt = item['datetime']
        if dt:
            match_date = dt.date()
            days_diff = (match_date - today).days
            if days_diff < 0:
                pass  # 忽略已过期
            elif days_diff == 0:
                time_ranges['今天'] += 1
            elif days_diff == 1:
                time_ranges['明天'] += 1
            elif days_diff <= 3:
                time_ranges['1-3天'] += 1
            elif days_diff <= 7:
                time_ranges['4-7天'] += 1
            elif days_diff <= 14:
                time_ranges['8-14天'] += 1
            elif days_diff <= 30:
                time_ranges['15-30天'] += 1
            else:
                time_ranges['30天以上'] += 1

    for range_name, count in time_ranges.items():
        bar = "█" * count + "░" * (max(0, 10 - count))
        output.append(f"  {range_name:>10}: {bar} {count} 场")

    # 赔率分布统计
    output.append(f"\n📊 赔率分布统计:")
    output.append("-" * 70)

    prob_ranges = {
        '90%+': 0,
        '80-90%': 0,
        '70-80%': 0,
        '60-70%': 0,
        '50-60%': 0,
        '<50%': 0
    }

    for item in all_matches_info:
        prob = item['win_prob']
        if prob >= 90:
            prob_ranges['90%+'] += 1
        elif prob >= 80:
            prob_ranges['80-90%'] += 1
        elif prob >= 70:
            prob_ranges['70-80%'] += 1
        elif prob >= 60:
            prob_ranges['60-70%'] += 1
        elif prob >= 50:
            prob_ranges['50-60%'] += 1
        else:
            prob_ranges['<50%'] += 1

    for range_name, count in prob_ranges.items():
        bar = "█" * count + "░" * (max(0, 10 - count))
        output.append(f"  {range_name:>10}: {bar} {count} 场")

    # 高概率比赛分析
    output.append(f"\n⭐ 高概率比赛推荐 (胜率>=80%):")
    output.append("-" * 70)

    high_prob = [item for item in all_matches_info if item['win_prob'] >= 80]
    high_prob.sort(key=lambda x: -x['win_prob'])

    if high_prob:
        for item in high_prob[:10]:
            match = item['match']
            output.append(f"  {match.get('match_date')} {match.get('match_time')} | {match.get('home_team', ''):>10} vs {match.get('away_team', ''):<10}")
            output.append(f"    胜率: {item['win_prob']:.1f}% | 赔率: 胜 {item['win_odds']:.2f} 平 {item['draw_odds']:.2f} 负 {item['lose_odds']:.2f}")
    else:
        output.append("  无高概率比赛")

    return "\n".join(output)


def filter_high_probability_matches(matches, days=3, min_probability=90, max_matches=5):
    """
    筛选高概率赢球的比赛

    Args:
        matches: 比赛列表
        days: 天数范围
        min_probability: 最低赢球概率（百分比）
        max_matches: 最大显示数量

    Returns:
        筛选后的比赛列表
    """
    now = datetime.now()
    today = now.date()
    cutoff_date = today + timedelta(days=days)

    high_prob_matches = []

    for match in matches:
        match_date_str = match.get('match_date', '')
        match_time_str = match.get('match_time', '')

        # 解析比赛时间
        match_datetime = None
        try:
            if match_date_str and match_time_str:
                # 支持 HH:MM 和 HH:MM:SS 格式
                time_format = '%H:%M:%S' if len(match_time_str.split(':')) == 3 else '%H:%M'
                match_datetime = datetime.strptime(
                    f"{match_date_str} {match_time_str}",
                    f"%Y-%m-%d {time_format}"
                )
            elif match_date_str:
                match_datetime = datetime.strptime(match_date_str, "%Y-%m-%d")
        except ValueError:
            continue

        if match_datetime is None:
            continue

        match_date = match_datetime.date()

        # 检查是否在时间范围内
        if not (today <= match_date <= cutoff_date):
            continue

        # 获取胜平负赔率
        had = match.get('had')
        if not had:
            continue

        win_odds = had.get('win', 0)
        draw_odds = had.get('draw', 0)
        lose_odds = had.get('lose', 0)

        if win_odds <= 0:
            continue

        # 计算隐含概率
        win_prob = calculate_implied_probability(win_odds)

        # 筛选指定概率以上的比赛
        if win_prob >= min_probability:
            high_prob_matches.append({
                'match': match,
                'win_prob': win_prob,
                'win_odds': win_odds,
                'draw_odds': draw_odds,
                'lose_odds': lose_odds,
                'match_datetime': match_datetime
            })

    # 按比赛时间排序
    high_prob_matches.sort(key=lambda x: x['match_datetime'])

    return high_prob_matches[:max_matches]


def format_output(results, min_probability=90):
    """格式化输出结果"""
    if not results:
        return f"未找到胜率 >= {min_probability}% 的比赛"

    output = []
    output.append("=" * 70)
    output.append("🏆 高概率赢球分析报告")
    output.append("=" * 70)
    output.append(f"筛选条件: 3天内开赛 + 胜率 >= {min_probability}%")
    output.append("-" * 70)

    for i, item in enumerate(results, 1):
        match = item['match']
        output.append(f"\n📅 第 {i} 场: {match.get('match_date', '未知日期')} {match.get('match_time', '')}")
        output.append(f"   🏟️  {match.get('home_team', '主队')} vs {match.get('away_team', '客队')}")
        output.append(f"   📊 胜率: {item['win_prob']:.1f}%")
        output.append(f"   💰 足彩赔率: 胜 {item['win_odds']:.2f} | 平 {item['draw_odds']:.2f} | 负 {item['lose_odds']:.2f}")
        output.append(f"   🏆 联赛: {match.get('league', '未知联赛')}")

        # 附加分析
        if item['win_prob'] >= 95:
            output.append(f"   ⭐⭐⭐ 强烈推荐! 胜率极高")
        elif item['win_prob'] >= 92:
            output.append(f"   ⭐⭐ 推荐投注")
        else:
            output.append(f"   ⭐ 可考虑投注")

        # 让球分析
        hhad = match.get('hhad')
        if hhad:
            goal_line = hhad.get('goal_line', '')
            if goal_line:
                output.append(f"   🎯 让球: {goal_line}")
                output.append(f"   📈 让球赔率: 胜 {hhad.get('win', '-')} | 平 {hhad.get('draw', '-')} | 负 {hhad.get('lose', '-')}")

    output.append("\n" + "=" * 70)
    output.append("⚠️ 风险提示: 博彩有风险，请理性投注！")
    output.append("=" * 70)

    return "\n".join(output)


def main():
    """主函数"""
    logger.info("正在获取体彩赔率数据...\n")

    try:
        # 创建体彩数据源
        provider = SportteryProvider('sporttery', {
            'pool_code': 'had,hhad,crs,ttg,bqc',
            'page_size': 100,
            'page_delay': 0.5,
            'timeout': 30
        })

        # 获取所有在售比赛
        all_matches = provider.fetch_all_play_types()

        if not all_matches:
            logger.info("未获取到任何比赛数据")
            return

        logger.info(f"获取到 {len(all_matches)} 场比赛\n")

        # 首先显示所有比赛及赔率分布
        print(show_all_matches(all_matches))

        # 筛选90%概率比赛（可能为空）
        high_prob_matches = filter_high_probability_matches(all_matches, min_probability=90)

        if high_prob_matches:
            output = format_output(high_prob_matches, min_probability=90)
            print(output)
        else:
            # 如果没有90%，显示接近90%的比赛
            print("\n" + "=" * 70)
            print("🏆 接近90%胜率的分析报告 (80%-90%)")
            print("=" * 70)
            print("注: 目前体彩暂无90%以上胜率比赛，以下为最接近的推荐:")
            print("-" * 70)

            # 筛选80%以上概率的比赛
            near_high_prob = filter_high_probability_matches(all_matches, min_probability=80)
            if near_high_prob:
                output = format_output(near_high_prob, min_probability=80)
                print(output)
            else:
                print("\n未找到胜率 >= 80% 的比赛")

            # 另外显示时间最接近的高概率比赛
            print("\n" + "=" * 70)
            print("📊 按时间排序的高概率比赛 (7天内开赛)")
            print("=" * 70)

            matches_7days = filter_high_probability_matches(all_matches, days=7, min_probability=60, max_matches=5)
            if matches_7days:
                for i, item in enumerate(matches_7days, 1):
                    match = item['match']
                    dt = item['match_datetime']
                    print(f"\n📅 第 {i} 场: {match.get('match_date')} {match.get('match_time')}")
                    print(f"   🏟️  {match.get('home_team')} vs {match.get('away_team')}")
                    print(f"   📊 胜率: {item['win_prob']:.1f}% | 赔率: 胜 {item['win_odds']:.2f} 平 {item['draw_odds']:.2f} 负 {item['lose_odds']:.2f}")
            else:
                print("7天内无符合条件的比赛")

    except Exception as e:
        logger.error(f"分析失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
