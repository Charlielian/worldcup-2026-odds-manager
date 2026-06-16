"""球队名称标准化工具。"""
import re


def normalize_team_name(name: str) -> str:
    """标准化队伍名称，处理不同格式的队伍名称。"""
    name = name.strip()

    if '欧洲' in name and '附加赛' in name and '胜者' in name:
        group_match = re.search(r'[A-Za-z0-9]', name)
        if group_match:
            group = group_match.group()
            return f'欧洲附加赛{group}组胜者'

    elif '洲际' in name and '附加赛' in name and '胜者' in name:
        group_match = re.search(r'[A-Za-z0-9]', name)
        if group_match:
            group = group_match.group()
            return f'洲际附加赛{group}组胜者'

    elif '沙特' in name:
        return '沙特阿拉伯'

    return name
