"""比赛与赔率表模型。"""
from sqlmodel import SQLModel, Field
from typing import Optional


class Match(SQLModel, table=True):
    __tablename__ = "matches"

    id: Optional[int] = Field(default=None, primary_key=True)
    team1: str = Field(index=True)
    team2: str = Field(index=True)
    match_time: str = Field(index=True)
    stage: str = Field(index=True)  # 小组赛/1/16决赛/...
    group_name: Optional[str] = Field(default=None, index=True)  # 小组赛组别
    status: str = Field(default="upcoming")  # upcoming/finished
    score1: Optional[int] = None
    score2: Optional[int] = None


class Odds(SQLModel, table=True):
    __tablename__ = "odds"

    id: Optional[int] = Field(default=None, primary_key=True)
    match_id: int = Field(foreign_key="matches.id", index=True)
    win_odds: float
    draw_odds: float
    lose_odds: float
    update_time: str = Field(index=True)
    source: str = Field(default="unknown")
