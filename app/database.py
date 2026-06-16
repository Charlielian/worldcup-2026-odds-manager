"""数据库引擎、Session 依赖与建表/Seed 逻辑。"""
import logging
import os
from typing import Generator

from sqlmodel import Session, SQLModel, create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool

logger = logging.getLogger(__name__)

# 避免在 import 阶段构建 engine
_engine: Engine | None = None


def get_database_path() -> str:
    return os.environ.get("DATABASE_PATH", "worldcup.db")


def build_engine() -> Engine:
    """构造 SQLAlchemy 引擎。"""
    db_path = get_database_path()
    url = f"sqlite:///./{db_path}"
    engine = create_engine(
        url,
        echo=False,
        connect_args={"check_same_thread": False},
        poolclass=QueuePool,
        pool_size=5,
        max_overflow=2,
        pool_pre_ping=True,
    )
    return engine


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        _engine = build_engine()
    return _engine


def get_session() -> Generator[Session, None, None]:
    """FastAPI 依赖：每次请求一个 Session。"""
    engine = get_engine()
    with Session(engine) as session:
        yield session


def create_db_and_tables() -> None:
    """建表（仅创建缺失表，不修改已有表）。"""
    engine = get_engine()
    # 显式 import 模型以注册 metadata
    from app.models.group import Group, Team
    from app.models.match import Match, Odds
    from app.models.knockout import KnockoutMatchup

    SQLModel.metadata.create_all(engine)
    logger.info("数据库表结构已创建/校验: %s", get_database_path())


def seed_initial_data() -> None:
    """初始化示例数据：仅在表为空时执行。"""
    engine = get_engine()
    from app.models.group import Group, Team
    from app.models.match import Match

    with Session(engine) as session:
        # 12 个小组
        if session.exec(text("SELECT COUNT(*) FROM groups")).first() == (0,):
            group_names = [f"{chr(ord('A') + i)}组" for i in range(12)]
            for name in group_names:
                session.add(Group(group_name=name))
            session.commit()

        # 48 支队伍（12 组 × 4 队）
        if session.exec(text("SELECT COUNT(*) FROM teams")).first() == (0,):
            teams_seed = [
                ("墨西哥", 1), ("南非", 1), ("韩国", 1), ("欧洲附加赛D组胜者", 1),
                ("加拿大", 2), ("欧洲附加赛A组胜者", 2), ("卡塔尔", 2), ("瑞士", 2),
                ("巴西", 3), ("摩洛哥", 3), ("海地", 3), ("苏格兰", 3),
                ("美国", 4), ("巴拉圭", 4), ("澳大利亚", 4), ("欧洲附加赛C组胜者", 4),
                ("德国", 5), ("库拉索", 5), ("科特迪瓦", 5), ("厄瓜多尔", 5),
                ("荷兰", 6), ("日本", 6), ("欧洲附加赛B组胜者", 6), ("突尼斯", 6),
                ("比利时", 7), ("埃及", 7), ("伊朗", 7), ("新西兰", 7),
                ("西班牙", 8), ("佛得角", 8), ("沙特阿拉伯", 8), ("乌拉圭", 8),
                ("法国", 9), ("塞内加尔", 9), ("洲际附加赛2组胜者", 9), ("挪威", 9),
                ("阿根廷", 10), ("阿尔及利亚", 10), ("奥地利", 10), ("约旦", 10),
                ("葡萄牙", 11), ("洲际附加赛1组胜者", 11), ("乌兹别克斯坦", 11), ("哥伦比亚", 11),
                ("英格兰", 12), ("克罗地亚", 12), ("加纳", 12), ("巴拿马", 12),
            ]
            for name, gid in teams_seed:
                session.add(Team(team_name=name, group_id=gid))
            session.commit()

        # 示例比赛
        if session.exec(text("SELECT COUNT(*) FROM matches")).first() == (0,):
            group_matches = [
                ("巴西", "塞尔维亚", "2026-06-15 18:00", "小组赛", "A组"),
                ("法国", "澳大利亚", "2026-06-16 15:00", "小组赛", "B组"),
                ("阿根廷", "沙特阿拉伯", "2026-06-17 21:00", "小组赛", "C组"),
                ("英格兰", "伊朗", "2026-06-18 18:00", "小组赛", "D组"),
                ("德国", "日本", "2026-06-19 15:00", "小组赛", "E组"),
                ("比利时", "加拿大", "2026-06-20 21:00", "小组赛", "F组"),
            ]
            for m in group_matches:
                session.add(Match(
                    team1=m[0], team2=m[1], match_time=m[2],
                    stage=m[3], group_name=m[4],
                ))

            knockout_matches = [
                ("巴西", "墨西哥", "2026-07-01 21:00", "淘汰赛"),
                ("法国", "波兰", "2026-07-02 18:00", "淘汰赛"),
                ("阿根廷", "厄瓜多尔", "2026-07-03 15:00", "淘汰赛"),
                ("英格兰", "塞内加尔", "2026-07-04 21:00", "淘汰赛"),
            ]
            for m in knockout_matches:
                session.add(Match(
                    team1=m[0], team2=m[1], match_time=m[2],
                    stage=m[3],
                ))
            session.commit()
