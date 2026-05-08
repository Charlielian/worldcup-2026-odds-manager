import os
import json


def load_odds_providers_config():
    """加载赔率数据源配置"""
    config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'odds_providers.json')
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Failed to load odds providers config: {e}")
        return {"providers": {"mock": {"enabled": True, "class": "MockOddsProvider", "priority": 99}}}


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
    DATABASE_PATH = os.environ.get('DATABASE_PATH', 'worldcup.db')
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:5173,http://localhost:5004').split(',')
    ADMIN_TOKEN = os.environ.get('ADMIN_TOKEN', 'wc2026-admin-token')
    DEBUG = os.environ.get('FLASK_ENV', 'development') == 'development'
    PORT = int(os.environ.get('PORT', 5004))
    
    # 赔率数据源配置
    ODDS_PROVIDERS = load_odds_providers_config()
