"""管理后台 API（需要 Bearer Token）。"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session

from app.deps import get_session
from app.security import admin_required
from app.services.match_service import (
    add_group_match,
    add_team_to_group,
    delete_team,
    generate_group_matches,
    get_all_group_matches,
    get_all_groups,
    get_group_name_by_id,
    get_match_by_id,
    get_teams_by_group,
    update_match_info,
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/admin",
    tags=["admin"],
    dependencies=[Depends(admin_required)],
)


class AddTeamPayload(BaseModel):
    team_name: str
    group_id: int


class GenerateMatchesPayload(BaseModel):
    group_id: int


class AddGroupMatchPayload(BaseModel):
    team1: str
    team2: str
    match_time: str
    group_name: str


class UpdateMatchPayload(BaseModel):
    team1: str
    team2: str
    match_time: str
    group_name: str
    status: str
    score1: Optional[int] = None
    score2: Optional[int] = None


@router.get("/groups")
def api_admin_groups(session: Session = Depends(get_session)):
    """获取所有小组及其队伍。"""
    try:
        groups = get_all_groups(session)
        groups_list = [{'id': g.id, 'group_name': g.group_name} for g in groups]
        group_teams = {}
        for g in groups:
            teams = get_teams_by_group(session, g.id)
            group_teams[g.id] = [{'id': t.id, 'team_name': t.team_name} for t in teams]
        return {'groups': groups_list, 'group_teams': group_teams}
    except Exception as e:
        logger.exception("api_admin_groups 失败")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/teams")
def api_admin_add_team(
    payload: AddTeamPayload,
    session: Session = Depends(get_session),
):
    """添加队伍到小组。"""
    try:
        if add_team_to_group(session, payload.team_name, payload.group_id):
            return {'status': 'success', 'message': '队伍添加成功'}
        raise HTTPException(
            status_code=400,
            detail='该小组已有4支队伍，无法继续添加',
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("api_admin_add_team 失败")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/teams/{team_id}")
def api_admin_delete_team(team_id: int, session: Session = Depends(get_session)):
    """删除队伍。"""
    try:
        delete_team(session, team_id)
        return {'status': 'success', 'message': '队伍已删除'}
    except Exception as e:
        logger.exception("api_admin_delete_team 失败")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/matches/generate")
def api_admin_generate_matches(
    payload: GenerateMatchesPayload,
    session: Session = Depends(get_session),
):
    """为指定小组生成比赛。"""
    try:
        group_name = get_group_name_by_id(session, payload.group_id)
        if not group_name:
            raise HTTPException(status_code=404, detail='小组不存在')
        generate_group_matches(session, payload.group_id, group_name)
        return {'status': 'success', 'message': '比赛生成成功'}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("api_admin_generate_matches 失败")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/group_matches")
def api_admin_add_group_match(
    payload: AddGroupMatchPayload,
    session: Session = Depends(get_session),
):
    """手动添加小组赛。"""
    try:
        add_group_match(
            session, payload.team1, payload.team2,
            payload.match_time, payload.group_name,
        )
        return {'status': 'success', 'message': '小组赛添加成功'}
    except Exception as e:
        logger.exception("api_admin_add_group_match 失败")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/matches")
def api_admin_matches(session: Session = Depends(get_session)):
    """获取所有小组赛比赛（管理用）。"""
    try:
        matches = get_all_group_matches(session)
        matches_list = [
            {
                'id': m.id, 'team1': m.team1, 'team2': m.team2,
                'match_time': m.match_time, 'stage': m.stage,
                'group_name': m.group_name, 'status': m.status,
                'score1': m.score1, 'score2': m.score2,
            }
            for m in matches
        ]
        return {'matches': matches_list}
    except Exception as e:
        logger.exception("api_admin_matches 失败")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/matches/{match_id}")
def api_admin_get_match(match_id: int, session: Session = Depends(get_session)):
    """获取单个比赛详情。"""
    try:
        m = get_match_by_id(session, match_id)
        if not m:
            raise HTTPException(status_code=404, detail='比赛不存在')
        return {
            'match': {
                'id': m.id, 'team1': m.team1, 'team2': m.team2,
                'match_time': m.match_time, 'stage': m.stage,
                'group_name': m.group_name, 'status': m.status,
                'score1': m.score1, 'score2': m.score2,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("api_admin_get_match 失败")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/matches/{match_id}")
def api_admin_update_match(
    match_id: int,
    payload: UpdateMatchPayload,
    session: Session = Depends(get_session),
):
    """更新比赛信息。"""
    try:
        update_match_info(
            session, match_id, payload.team1, payload.team2,
            payload.match_time, payload.group_name, payload.status,
            payload.score1, payload.score2,
        )
        return {'status': 'success', 'message': '比赛信息已更新'}
    except Exception as e:
        logger.exception("api_admin_update_match 失败")
        raise HTTPException(status_code=500, detail=str(e))
