"""小组与队伍表模型。"""
from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional


class Group(SQLModel, table=True):
    __tablename__ = "groups"

    id: Optional[int] = Field(default=None, primary_key=True)
    group_name: str = Field(unique=True, index=True)

    teams: List["Team"] = Relationship(back_populates="group")


class Team(SQLModel, table=True):
    __tablename__ = "teams"

    id: Optional[int] = Field(default=None, primary_key=True)
    team_name: str = Field(index=True)
    group_id: int = Field(foreign_key="groups.id")

    group: Optional[Group] = Relationship(back_populates="teams")
