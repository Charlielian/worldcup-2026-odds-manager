import logging
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, redirect, url_for

from backend.utils.flags import FLAG_MAP
from backend.services.match_service import (
    get_matches_by_date,
    get_upcoming_matches,
    group_matches_by_date,
    get_next_match_date,
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

templates_bp = Blueprint('templates', __name__)


@templates_bp.route('/')
def index():
    date = request.args.get('date')
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")

    day_matches = get_matches_by_date(date)

    if not day_matches and date == datetime.now().strftime("%Y-%m-%d"):
        next_date = get_next_match_date()
        if next_date != date:
            return redirect(f'/?date={next_date}')

    tomorrow = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    upcoming_matches = get_upcoming_matches(tomorrow, 7)
    grouped_upcoming = group_matches_by_date(upcoming_matches)

    return render_template('index.html', date=date, day_matches=day_matches, grouped_upcoming=grouped_upcoming, flag_map=FLAG_MAP)


@templates_bp.route('/<date>')
def index_with_date(date):
    day_matches = get_matches_by_date(date)

    if not day_matches and date == datetime.now().strftime("%Y-%m-%d"):
        next_date = get_next_match_date()
        if next_date != date:
            return redirect(f'/?date={next_date}')

    tomorrow = (datetime.strptime(date, "%Y-%m-%d") + timedelta(days=1)).strftime("%Y-%m-%d")
    upcoming_matches = get_upcoming_matches(tomorrow, 7)
    grouped_upcoming = group_matches_by_date(upcoming_matches)

    return render_template('index.html', date=date, day_matches=day_matches, grouped_upcoming=grouped_upcoming, flag_map=FLAG_MAP)


@templates_bp.route('/group_stage')
@templates_bp.route('/group_stage/<group>')
def group_stage(group=None):
    matches = get_group_matches(group)
    return render_template('group_stage.html', matches=matches, current_group=group, flag_map=FLAG_MAP)


@templates_bp.route('/knockout')
def knockout():
    matches = get_knockout_matches()
    return render_template('knockout.html', matches=matches, flag_map=FLAG_MAP)


@templates_bp.route('/knockout/bracket')
def knockout_bracket():
    bracket_data = get_knockout_bracket_data()
    return render_template('knockout_bracket.html', bracket_data=bracket_data, flag_map=FLAG_MAP)


@templates_bp.route('/rankings')
@templates_bp.route('/rankings/<group>')
def rankings(group=None):
    group_rankings = get_group_rankings(group)
    return render_template('rankings.html', group_rankings=group_rankings, flag_map=FLAG_MAP, current_group=group)


@templates_bp.route('/update_result', methods=['POST'])
def update_result():
    match_id = request.form['match_id']
    score1 = request.form['score1']
    score2 = request.form['score2']
    update_match_result(match_id, score1, score2)
    return {'status': 'success', 'message': '比赛结果已更新'}


@templates_bp.route('/admin')
def admin():
    return redirect(url_for('templates.group_team_management'))


@templates_bp.route('/admin/group_team_management')
def group_team_management():
    groups = get_all_groups()

    group_teams = {}
    for group in groups:
        group_id = group[0]
        group_teams[group_id] = get_teams_by_group(group_id)

    return render_template('group_team_management.html', groups=groups, group_teams=group_teams)


@templates_bp.route('/admin/match_management')
def match_management():
    matches = get_all_group_matches()
    return render_template('match_management.html', matches=matches)


@templates_bp.route('/admin/match_generation')
def match_generation():
    groups = get_all_groups()

    group_teams = {}
    for group in groups:
        group_id = group[0]
        group_teams[group_id] = get_teams_by_group(group_id)

    return render_template('match_generation.html', groups=groups, group_teams=group_teams)


@templates_bp.route('/admin/add_team', methods=['POST'])
def add_team():
    team_name = request.form['team_name']
    group_id = request.form['group_id']
    success = add_team_to_group(team_name, group_id)
    return redirect(url_for('templates.group_team_management'))


@templates_bp.route('/admin/delete_team', methods=['POST'])
def delete_team_route():
    team_id = request.form['team_id']
    delete_team(team_id)
    return redirect(url_for('templates.group_team_management'))


@templates_bp.route('/admin/generate_matches', methods=['POST'])
def generate_matches():
    group_id = request.form['generate_group_id']

    # 使用连接池获取小组名称（修复原 app.py 直接创建 sqlite3 连接的问题）
    group_name = get_group_name_by_id(group_id)
    if group_name:
        generate_group_matches(group_id, group_name)

    return redirect(url_for('templates.admin'))


@templates_bp.route('/admin/add_group_match', methods=['POST'])
def add_group_match_route():
    team1 = request.form['team1']
    team2 = request.form['team2']
    match_time = request.form['match_time']
    group_name = request.form['group_name']
    add_group_match(team1, team2, match_time, group_name)
    return redirect(url_for('templates.admin'))


@templates_bp.route('/admin/edit_match/<match_id>')
def edit_match(match_id):
    match = get_match_by_id(match_id)
    return render_template('edit_match.html', match=match)


@templates_bp.route('/admin/update_match/<match_id>', methods=['POST'])
def update_match(match_id):
    team1 = request.form['team1']
    team2 = request.form['team2']
    match_time = request.form['match_time']
    group_name = request.form['group_name']
    status = request.form['status']
    score1 = request.form['score1'] if request.form['score1'] else None
    score2 = request.form['score2'] if request.form['score2'] else None
    update_match_info(match_id, team1, team2, match_time, group_name, status, score1, score2)
    return redirect(url_for('templates.admin'))
