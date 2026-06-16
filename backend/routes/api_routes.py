import logging
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify

from backend.db import serialize_match
from backend.utils.auth import admin_required
from backend.services.match_service import (
    get_matches_by_date,
    get_upcoming_matches,
    group_matches_by_date,
    get_group_matches,
    get_knockout_matches,
    get_all_group_matches,
    add_group_match,
    get_all_groups,
    get_teams_by_group,
    add_team_to_group,
    delete_team,
    generate_group_matches,
    get_match_by_id,
    update_match_info,
    update_match_result,
    get_group_name_by_id,
)
from backend.services.ranking_service import get_group_rankings
from backend.services.knockout_service import get_knockout_bracket_data

logger = logging.getLogger(__name__)

api_bp = Blueprint('api', __name__)


# --- 比赛相关 API ---

@api_bp.route('/api/v1/matches')
def api_matches():
    """获取比赛列表。支持 ?date=YYYY-MM-DD 查询参数。"""
    try:
        date = request.args.get('date')
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")

        day_matches_raw = get_matches_by_date(date)
        day_matches = [serialize_match(m, o) for m, o in day_matches_raw]

        tomorrow = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
        upcoming_raw = get_upcoming_matches(tomorrow, 7)
        upcoming_matches = [serialize_match(m, o) for m, o in upcoming_raw]

        grouped_raw = group_matches_by_date(upcoming_raw)
        grouped_upcoming = {}
        for g_date, items in grouped_raw.items():
            grouped_upcoming[g_date] = [serialize_match(m, o) for m, o in items]

        return jsonify({
            'day_matches': day_matches,
            'upcoming_matches': upcoming_matches,
            'grouped_upcoming': grouped_upcoming
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/api/v1/matches/<int:match_id>/result', methods=['POST'])
def api_update_result(match_id):
    """更新比赛结果。支持 JSON body 和 form data。"""
    try:
        if request.is_json:
            data = request.get_json()
            score1 = data.get('score1')
            score2 = data.get('score2')
        else:
            score1 = request.form.get('score1')
            score2 = request.form.get('score2')

        if score1 is None or score2 is None:
            return jsonify({'status': 'error', 'message': '缺少 score1 或 score2 参数'}), 400

        update_match_result(match_id, score1, score2)
        return jsonify({'status': 'success', 'message': '比赛结果已更新'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


# --- 小组赛相关 API ---

@api_bp.route('/api/v1/group_stage')
def api_group_stage():
    """获取小组赛比赛。支持 ?group=X 查询参数。"""
    try:
        group = request.args.get('group')
        matches_raw = get_group_matches(group)
        matches = [serialize_match(m, o) for m, o in matches_raw]
        current_group = group if group else ''
        return jsonify({
            'matches': matches,
            'current_group': current_group
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# --- 淘汰赛相关 API ---

@api_bp.route('/api/v1/knockout')
def api_knockout():
    """获取淘汰赛比赛列表。"""
    try:
        matches_raw = get_knockout_matches()
        matches = [serialize_match(m, o) for m, o in matches_raw]
        return jsonify({
            'matches': matches
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/api/v1/knockout/bracket')
def api_knockout_bracket():
    """获取淘汰赛对阵图数据。"""
    try:
        bracket_data = get_knockout_bracket_data()
        return jsonify({
            'bracket_data': bracket_data
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# --- 排名相关 API ---

@api_bp.route('/api/v1/rankings')
def api_rankings():
    """获取小组排名。支持 ?group=X 查询参数。"""
    try:
        group = request.args.get('group')
        rankings = get_group_rankings(group)
        current_group = group if group else ''
        return jsonify({
            'rankings': rankings,
            'current_group': current_group
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# --- 国旗 API ---

@api_bp.route('/api/v1/flags')
def api_flags():
    """返回国旗映射字典（供前端使用）。"""
    from backend.utils.flags import get_flag_map_dict
    return jsonify(get_flag_map_dict())


@api_bp.route('/api/v1/odds/sources')
def api_odds_sources():
    """返回赔率数据源列表和状态。"""
    from backend.services.odds_service import get_odds_sources
    return jsonify({
        'sources': get_odds_sources()
    })


@api_bp.route('/api/v1/odds/update', methods=['POST'])
@admin_required
def api_odds_update():
    """手动触发赔率更新（管理用）。"""
    from backend.services.odds_service import update_odds
    try:
        updated, skipped = update_odds()
        return jsonify({
            'status': 'success',
            'message': f'赔率更新完成: 成功 {updated} 场, 跳过 {skipped} 场',
            'updated': updated,
            'skipped': skipped
        })
    except Exception as e:
        logger.error(f"手动更新赔率失败: {e}")
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/api/v1/live/matches')
def api_live_matches():
    """获取体彩当前在售比赛及全部玩法赔率（胜平负/让球/比分/总进球/半全场）。
    同时补充本地数据库中但体彩没有的比赛。"""
    from backend.services.sporttery_provider import SportteryProvider

    try:
        # 1. 获取体彩API数据
        provider = SportteryProvider('sporttery', {
            'pool_code': 'had,hhad,crs,ttg,hafu',
            'page_size': 100,
            'page_delay': 0.5,
            'timeout': 30
        })

        sporttery_matches = provider.fetch_all_play_types()

        # 2. 构建体彩比赛索引：使用 (规范化主队, 规范化客队, 日期) 作为唯一键
        import backend.db
        from datetime import datetime, timedelta
        import re

        def normalize_team(name):
            """智能队伍名称规范化：去除空格、括号内容、特殊字符，统一常见简称"""
            if not name:
                return ''
            # 去除所有空白字符
            result = re.sub(r'[\s()（）【】\[\]]', '', name)
            # 去除常见后缀简化
            result = result.replace('共和国', '').replace('共和国', '')
            # 归一化常见简称（去除队名
            return result.strip()

        def make_key(team1, team2, date):
            """生成比赛唯一键（使用frozenset([(规范化队伍对，忽略顺序，加日期"""
            t1 = normalize_team(team1)
            t2 = normalize_team(team2)
            return (frozenset([t1, t2]), date[:10] if date else '')

        # 构建体彩比赛集合（队伍对，日期）作为键
        sporttery_keys = set()
        for m in sporttery_matches:
            key = make_key(m.get('home_team', ''), m.get('away_team', ''), m.get('match_date', ''))
            sporttery_keys.add(key)

        # 3. 获取本地数据库中未来的比赛（upcoming）
        local_conn = backend.db.db_pool.get_connection()
        try:
            local_cursor = local_conn.cursor()

            local_cursor.execute('''
                SELECT m.id, m.team1, m.team2, m.match_time, m.stage, m.status, m.score1, m.score2, m.group_name,
                       o.win_odds, o.draw_odds, o.lose_odds, o.update_time, o.source
                FROM matches m
                LEFT JOIN (
                    SELECT match_id, win_odds, draw_odds, lose_odds, update_time, source
                    FROM odds o1
                    WHERE o1.ROWID = (
                        SELECT o2.ROWID FROM odds o2
                        WHERE o2.match_id = o1.match_id
                        ORDER BY o2.update_time DESC, o2.ROWID DESC
                        LIMIT 1
                    )
                ) o ON m.id = o.match_id
                WHERE m.status = 'upcoming'
                ORDER BY m.match_time
            ''')

            local_rows = local_cursor.fetchall()

            # 补充本地数据库比赛：补充到比赛数
            match_num_counter = len(sporttery_matches)
            for row in local_rows:
                match_id, team1, team2, match_time, stage, status, score1, score2, group_name, \
                    win_odds, draw_odds, lose_odds, odds_update_time, odds_source = row

                # 日期从 match_time 中提取
                date_part = ''
                time_part = ''
                if match_time:
                    try:
                        dt = datetime.strptime(match_time, '%Y-%m-%d %H:%M:%S')
                        date_part = dt.strftime('%Y-%m-%d')
                        time_part = dt.strftime('%H:%M')
                    except (ValueError, TypeError):
                        date_part = str(match_time)[:10]
                        time_part = str(match_time)[11:16] or '00:00'

                # 检查是否在体彩API中已存在
                key = make_key(team1, team2, date_part)
                if key in sporttery_keys:
                    continue

                # 检查队伍检查：队名前缀/后缀简化后再比较
                # 如"阿尔及利"与"阿尔及利亚"的比较时需要进一步检查
                found = False
                for s_key in sporttery_keys:
                    s_teams, s_date = s_key
                    if s_date == date_part[:10]:
                        # 日期相同，检查队名是否包含关系
                        local_teams_normalized = [normalize_team(team1), normalize_team(team2)]
                        for s_team_pair in s_teams:
                            # 检查每一个本地队是否以体彩队名为前缀或反之
                            for local_t in local_teams_normalized:
                                if local_t.startswith(normalize_team(s_team_pair)) or normalize_team(s_team_pair).startswith(local_t):
                                    found = True
                                    break
                            if found:
                                break
                    if found:
                        break
                if found:
                    continue

                match_num_counter += 1
                num_str = f'{match_num_counter:03d}'

                match_dict = {
                    'match_num': num_str,
                    'match_date': date_part,
                    'match_time': time_part,
                    'home_team': team1,
                    'away_team': team2,
                    'league': stage or '世界杯',
                }

                if win_odds or draw_odds or lose_odds:
                    match_dict['had'] = {
                        'win': float(win_odds) if win_odds else None,
                        'draw': float(draw_odds) if draw_odds else None,
                        'lose': float(lose_odds) if lose_odds else None,
                        'update_time': odds_update_time or '',
                    }

                sporttery_matches.append(match_dict)

        finally:
            backend.db.db_pool.return_connection(local_conn)

        # 4. 按日期分组
        matches_by_date = {}
        for m in sporttery_matches:
            date_str = m.get('match_date', '未知日期')
            if date_str not in matches_by_date:
                matches_by_date[date_str] = []
            matches_by_date[date_str].append(m)

        # 5. 每个日期内按时间排序
        for date_str in matches_by_date:
            matches_by_date[date_str].sort(key=lambda x: x.get('match_time', ''))

        return jsonify({
            'total': len(sporttery_matches),
            'matches_by_date': matches_by_date,
            'all_matches': sporttery_matches
        })
    except Exception as e:
        logger.error(f"获取体彩实时数据失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return jsonify({'status': 'error', 'message': str(e), 'total': 0, 'matches_by_date': {}, 'all_matches': []}), 500


# --- 管理后台 API ---

@api_bp.route('/api/v1/admin/groups')
@admin_required
def api_admin_groups():
    """获取所有小组及其队伍。"""
    try:
        groups = get_all_groups()
        groups_list = [{'id': g[0], 'group_name': g[1]} for g in groups]

        group_teams = {}
        for group in groups:
            group_id = group[0]
            teams = get_teams_by_group(group_id)
            group_teams[group_id] = [{'id': t[0], 'team_name': t[1]} for t in teams]

        return jsonify({
            'groups': groups_list,
            'group_teams': group_teams
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/api/v1/admin/teams', methods=['POST'])
@admin_required
def api_admin_add_team():
    """添加队伍到小组。"""
    try:
        if request.is_json:
            data = request.get_json()
            team_name = data.get('team_name')
            group_id = data.get('group_id')
        else:
            team_name = request.form.get('team_name')
            group_id = request.form.get('group_id')

        if not team_name or not group_id:
            return jsonify({'status': 'error', 'message': '缺少 team_name 或 group_id 参数'}), 400

        success = add_team_to_group(team_name, group_id)
        if success:
            return jsonify({'status': 'success', 'message': '队伍添加成功'})
        else:
            return jsonify({'status': 'error', 'message': '该小组已有4支队伍，无法继续添加'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/api/v1/admin/teams/<int:team_id>', methods=['DELETE'])
@admin_required
def api_admin_delete_team(team_id):
    """删除队伍。"""
    try:
        delete_team(team_id)
        return jsonify({'status': 'success', 'message': '队伍已删除'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/api/v1/admin/matches/generate', methods=['POST'])
@admin_required
def api_admin_generate_matches():
    """为指定小组生成比赛。"""
    try:
        if request.is_json:
            data = request.get_json()
            group_id = data.get('group_id')
        else:
            group_id = request.form.get('group_id')

        if not group_id:
            return jsonify({'status': 'error', 'message': '缺少 group_id 参数'}), 400

        # 使用连接池获取小组名称（修复原 app.py 直接创建 sqlite3 连接的问题）
        group_name = get_group_name_by_id(group_id)
        if not group_name:
            return jsonify({'status': 'error', 'message': '小组不存在'}), 404

        generate_group_matches(group_id, group_name)
        return jsonify({'status': 'success', 'message': '比赛生成成功'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/api/v1/admin/group_matches', methods=['POST'])
@admin_required
def api_admin_add_group_match():
    """手动添加小组赛。"""
    try:
        if request.is_json:
            data = request.get_json()
            team1 = data.get('team1')
            team2 = data.get('team2')
            match_time = data.get('match_time')
            group_name = data.get('group_name')
        else:
            team1 = request.form.get('team1')
            team2 = request.form.get('team2')
            match_time = request.form.get('match_time')
            group_name = request.form.get('group_name')

        if not all([team1, team2, match_time, group_name]):
            return jsonify({'status': 'error', 'message': '缺少必要参数 (team1, team2, match_time, group_name)'}), 400

        add_group_match(team1, team2, match_time, group_name)
        return jsonify({'status': 'success', 'message': '小组赛添加成功'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500


@api_bp.route('/api/v1/admin/matches')
@admin_required
def api_admin_matches():
    """获取所有小组赛比赛（管理用）。"""
    try:
        matches = get_all_group_matches()
        matches_list = []
        for m in matches:
            matches_list.append({
                'id': m[0],
                'team1': m[1],
                'team2': m[2],
                'match_time': m[3],
                'stage': m[4],
                'group_name': m[5],
                'status': m[6],
                'score1': m[7],
                'score2': m[8]
            })
        return jsonify({
            'matches': matches_list
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/api/v1/admin/matches/<int:match_id>')
@admin_required
def api_admin_get_match(match_id):
    """获取单个比赛详情。"""
    try:
        match = get_match_by_id(match_id)
        if match is None:
            return jsonify({'error': '比赛不存在'}), 404

        match_dict = {
            'id': match[0],
            'team1': match[1],
            'team2': match[2],
            'match_time': match[3],
            'stage': match[4],
            'group_name': match[5],
            'status': match[6],
            'score1': match[7],
            'score2': match[8]
        }
        return jsonify({
            'match': match_dict
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@api_bp.route('/api/v1/admin/matches/<int:match_id>', methods=['PUT'])
@admin_required
def api_admin_update_match(match_id):
    """更新比赛信息。"""
    try:
        if request.is_json:
            data = request.get_json()
            team1 = data.get('team1')
            team2 = data.get('team2')
            match_time = data.get('match_time')
            group_name = data.get('group_name')
            status = data.get('status')
            score1 = data.get('score1')
            score2 = data.get('score2')
        else:
            team1 = request.form.get('team1')
            team2 = request.form.get('team2')
            match_time = request.form.get('match_time')
            group_name = request.form.get('group_name')
            status = request.form.get('status')
            score1 = request.form.get('score1')
            score2 = request.form.get('score2')

        if not all([team1, team2, match_time, group_name, status]):
            return jsonify({'status': 'error', 'message': '缺少必要参数'}), 400

        update_match_info(match_id, team1, team2, match_time, group_name, status, score1, score2)
        return jsonify({'status': 'success', 'message': '比赛信息已更新'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
