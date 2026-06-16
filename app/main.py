"""FastAPI 入口。"""
import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from app.config import get_settings
from app.database import create_db_and_tables, get_engine, seed_initial_data
from app.routers import (
    admin as admin_router,
    flags as flags_router,
    groups as groups_router,
    knockout as knockout_router,
    live as live_router,
    matches as matches_router,
    odds as odds_router,
)
from app.services.knockout_service import (
    init_knockout_matchups, update_knockout_teams,
)
from app.services.odds_service import (
    init_crawler_manager, update_odds_sync,
)

logger = logging.getLogger(__name__)

ODDS_UPDATE_INTERVAL = 3600  # 秒


async def _odds_update_loop():
    """异步循环：每小时更新一次赔率。"""
    while True:
        try:
            # 把同步 requests 调用放到线程池
            await asyncio.to_thread(_do_update_odds)
        except Exception as e:
            logger.error(f"赔率更新失败: {e}")
        await asyncio.sleep(ODDS_UPDATE_INTERVAL)


def _do_update_odds():
    """同步执行：在线程中跑赔率更新。"""
    engine = get_engine()
    with Session(engine) as session:
        try:
            updated, skipped = update_odds_sync(session)
            logger.info(f"赔率更新完成: 成功 {updated} 场, 跳过 {skipped} 场")
        except Exception as e:
            logger.error(f"赔率更新异常: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动 / 关闭钩子。"""
    settings = get_settings()
    logging.basicConfig(
        level=logging.DEBUG if settings.DEBUG else logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    )

    # 1. 建表
    create_db_and_tables()

    # 2. Seed 初始数据
    seed_initial_data()

    # 3. 初始化淘汰赛对阵
    engine = get_engine()
    with Session(engine) as session:
        init_knockout_matchups(session)
        update_knockout_teams(session)

    # 4. 初始化赔率爬虫
    init_crawler_manager(settings.ODDS_PROVIDERS.get('providers', {}))
    logger.info(f"赔率数据源配置: {list(settings.ODDS_PROVIDERS.get('providers', {}).keys())}")

    # 5. 首次赔率更新（同步执行，阻塞启动直到完成）
    _do_update_odds()

    # 6. 启动后台定时任务
    task = asyncio.create_task(_odds_update_loop())

    logger.info("启动服务器: port=%s, debug=%s", settings.PORT, settings.DEBUG)

    try:
        yield
    finally:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="2026 世界杯赛事管理系统",
        version="2.0.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(matches_router.router)
    app.include_router(groups_router.router)
    app.include_router(knockout_router.router)
    app.include_router(live_router.router)
    app.include_router(odds_router.router)
    app.include_router(flags_router.router)
    app.include_router(admin_router.router)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=False,
    )
