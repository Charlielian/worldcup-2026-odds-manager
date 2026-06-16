"""淘汰赛对阵表模型。"""
from sqlmodel import SQLModel, Field
from typing import Optional


class KnockoutMatchup(SQLModel, table=True):
    __tablename__ = "knockout_matchups"

    id: Optional[int] = Field(default=None, primary_key=True)
    match_number: int
    round_name: str = Field(index=True)
    position: str
    slot1_team_group: Optional[str] = None
    slot2_team_group: Optional[str] = None
    venue: Optional[str] = None
    match_time: Optional[str] = None
    bracket_code: Optional[str] = Field(default=None, index=True)
    allowed_third_groups: Optional[str] = None
