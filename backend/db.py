import sqlite3
import queue
import logging
from sqlite3 import Error
from contextlib import contextmanager

from backend.utils.flags import get_flag

logger = logging.getLogger(__name__)


class DatabaseConnectionPool:
    """线程安全的 SQLite 数据库连接池。"""

    def __init__(self, db_path, max_connections=5):
        self.db_path = db_path
        self.max_connections = max_connections
        self.connections = queue.Queue(max_connections)

        for _ in range(max_connections):
            try:
                conn = sqlite3.connect(db_path)
                conn.row_factory = sqlite3.Row
                self.connections.put(conn)
            except Error as e:
                logger.error("创建数据库连接失败: %s", e)

    def get_connection(self, timeout=5):
        """从连接池获取一个连接，带超时和健康检查。"""
        try:
            conn = self.connections.get(timeout=timeout)
        except queue.Empty:
            logger.warning("连接池超时，创建新连接")
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row
            return conn

        # 健康检查：如果连接已关闭或损坏，创建新连接
        try:
            conn.execute("SELECT 1")
        except (Error, OSError):
            logger.warning("连接已损坏，重新创建")
            try:
                conn.close()
            except Error:
                pass
            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row

        return conn

    def return_connection(self, conn):
        if conn:
            try:
                self.connections.put_nowait(conn)
            except queue.Full:
                logger.warning("连接池已满，关闭多余连接")
                try:
                    conn.close()
                except Error:
                    pass

    def close_all(self):
        while not self.connections.empty():
            try:
                conn = self.connections.get_nowait()
                conn.close()
            except Error as e:
                logger.error("关闭数据库连接失败: %s", e)


# 初始化数据库连接池（延迟到 create_app 中通过 init_db 调用）
db_pool = None


def init_db_pool(db_path):
    """初始化全局数据库连接池。"""
    global db_pool
    db_pool = DatabaseConnectionPool(db_path)
    logger.info("数据库连接池初始化完成: %s", db_path)


@contextmanager
def get_db():
    """上下文管理器：从连接池获取连接，使用完毕后自动归还。"""
    conn = db_pool.get_connection()
    try:
        yield conn
    finally:
        db_pool.return_connection(conn)


def row_to_dict(row, columns):
    """将 sqlite3.Row 对象转换为字典。

    Args:
        row: sqlite3.Row 实例
        columns: 列名列表

    Returns:
        dict
    """
    if row is None:
        return None
    return {col: row[col] for col in columns}


def serialize_match(match_tuple, odds_tuple=None):
    """将比赛元组转换为干净的字典。

    match_tuple 期望顺序: (id, team1, team2, match_time, stage, status, score1, score2, group_name)
    odds_tuple 期望顺序: (win_odds, draw_odds, lose_odds, update_time, source)

    Returns:
        dict
    """
    result = {
        'id': match_tuple[0],
        'team1': match_tuple[1],
        'team2': match_tuple[2],
        'match_time': match_tuple[3],
        'stage': match_tuple[4],
        'status': match_tuple[5],
        'score1': match_tuple[6],
        'score2': match_tuple[7],
        'group_name': match_tuple[8] if len(match_tuple) > 8 else None,
        'flag1': get_flag(match_tuple[1]),
        'flag2': get_flag(match_tuple[2]),
    }

    if odds_tuple:
        result['odds'] = {
            'win_odds': odds_tuple[0],
            'draw_odds': odds_tuple[1],
            'lose_odds': odds_tuple[2],
            'update_time': odds_tuple[3],
            'source': odds_tuple[4] if len(odds_tuple) > 4 else 'unknown',
        }

    return result


def get_matches_with_odds_joined(cursor, where_clause, params=()):
    """使用单个 JOIN 查询获取比赛及其最新赔率，避免 N+1 查询。

    Args:
        cursor: 数据库游标
        where_clause: WHERE 子句（不含 WHERE 关键字）
        params: 查询参数

    Returns:
        list of (match_tuple, odds_tuple_or_None)
    """
    query = f"""
        SELECT m.id, m.team1, m.team2, m.match_time, m.stage, m.status, m.score1, m.score2, m.group_name,
               o.win_odds, o.draw_odds, o.lose_odds, o.update_time, o.source
        FROM matches m
        LEFT JOIN (
            SELECT match_id, win_odds, draw_odds, lose_odds, update_time, source
            FROM odds o1
            WHERE update_time = (SELECT MAX(update_time) FROM odds o2 WHERE o2.match_id = o1.match_id)
        ) o ON m.id = o.match_id
        WHERE {where_clause}
        ORDER BY m.match_time
    """
    cursor.execute(query, params)
    rows = cursor.fetchall()
    result = []
    for row in rows:
        match_tuple = (row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8])
        odds_tuple = (row[9], row[10], row[11], row[12], row[13]) if row[9] is not None else None
        result.append((match_tuple, odds_tuple))
    return result
