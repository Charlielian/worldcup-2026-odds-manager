import os
import sys
import threading
import time
import logging

logger = logging.getLogger(__name__)


def scheduled_task(app):
    """后台任务：每小时更新赔率。"""
    with app.app_context():
        from backend.services.odds_service import update_odds
        while True:
            try:
                updated, skipped = update_odds()
                logger.info(f"赔率更新完成: 成功 {updated} 场, 跳过 {skipped} 场")
            except Exception as e:
                logger.error(f"赔率更新失败: {e}")
            time.sleep(3600)


def main():
    from backend import create_app
    from backend.config import Config

    app = create_app(Config)

    with app.app_context():
        # 初始化数据库连接池
        from backend.db import init_db_pool
        init_db_pool(app.config['DATABASE_PATH'])

        # 初始化数据库表结构和示例数据
        from backend.services.match_service import init_db
        init_db()

        # 初始化淘汰赛
        from backend.services.knockout_service import init_knockout_matchups, update_knockout_teams
        init_knockout_matchups()
        update_knockout_teams()

        # 初始化赔率爬虫管理器
        from backend.services.odds_service import init_crawler_manager
        odds_config = app.config.get('ODDS_PROVIDERS', {})
        init_crawler_manager(odds_config.get('providers', {}))
        logger.info(f"赔率数据源配置: {odds_config.get('providers', {}).keys()}")

        # 初始赔率更新
        from backend.services.odds_service import update_odds
        updated, skipped = update_odds()
        logger.info(f"初始赔率更新: 成功 {updated} 场, 跳过 {skipped} 场")

    # 启动后台定时任务
    task_thread = threading.Thread(target=scheduled_task, args=(app,), daemon=True)
    task_thread.start()

    logger.info("启动服务器: port=%s, debug=%s", app.config['PORT'], app.config['DEBUG'])
    app.run(debug=app.config['DEBUG'], host='0.0.0.0', port=app.config['PORT'])


if __name__ == '__main__':
    main()
