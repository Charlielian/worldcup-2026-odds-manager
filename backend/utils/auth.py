from functools import wraps
from flask import request, jsonify, current_app


def admin_required(f):
    """装饰器：要求在 Authorization 头或查询参数中提供有效的管理员令牌。"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
        if not token:
            token = request.args.get('token')
        if not token or token != current_app.config['ADMIN_TOKEN']:
            return jsonify({'status': 'error', 'message': '未授权访问'}), 401
        return f(*args, **kwargs)
    return decorated
