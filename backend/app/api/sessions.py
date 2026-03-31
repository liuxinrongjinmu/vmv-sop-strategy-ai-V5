from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import json
import logging

from app.core.database import get_session
from app.models.models import Session as SessionModel
from app.schemas.schemas import SessionCreate, SessionUpdate, SessionResponse, SessionDetail
from app.services.file_parser import FileParser

router = APIRouter(prefix="/api/sessions", tags=["sessions"])
logger = logging.getLogger(__name__)

@router.post("", response_model=SessionResponse)
async def create_session(
    session_data: SessionCreate,
    db: AsyncSession = Depends(get_session)
):
    """
    创建新会话
    接收VMV和基本信息，初始化会话状态
    """
    logger.info(f"收到创建会话请求: company_name={session_data.company_name}, industry={session_data.industry}")
    
    # 合并附加信息
    combined_info = session_data.additional_info or ""
    
    session = SessionModel(
        vision=session_data.vision,
        mission=session_data.mission,
        values=session_data.values,
        company_name=session_data.company_name,
        industry=session_data.industry,
        stage=session_data.stage,
        team_size=session_data.team_size,
        selected_track=session_data.selected_track,
        additional_info=combined_info,
        current_stage=1,
        status="active"
    )
    
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    return SessionResponse(
        session_id=session.session_id,
        current_stage=session.current_stage,
        status=session.status,
        created_at=session.created_at
    )

@router.get("/{session_id}", response_model=SessionDetail)
async def get_session(
    session_id: str,
    db: AsyncSession = Depends(get_session)
):
    """
    获取会话详情
    """
    result = await db.execute(
        select(SessionModel).where(SessionModel.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    return SessionDetail(
        session_id=session.session_id,
        current_stage=session.current_stage,
        status=session.status,
        created_at=session.created_at,
        vision=session.vision,
        mission=session.mission,
        values=session.values,
        company_name=session.company_name,
        industry=session.industry,
        stage=session.stage,
        team_size=session.team_size,
        selected_track=session.selected_track,
        additional_info=session.additional_info
    )

@router.put("/{session_id}", response_model=SessionDetail)
async def update_session(
    session_id: str,
    data: SessionUpdate,
    db: AsyncSession = Depends(get_session)
):
    """
    更新会话信息
    """
    result = await db.execute(
        select(SessionModel).where(SessionModel.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 更新字段
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(session, key, value)
    
    await db.commit()
    await db.refresh(session)
    
    return SessionDetail(
        session_id=session.session_id,
        current_stage=session.current_stage,
        status=session.status,
        created_at=session.created_at,
        vision=session.vision,
        mission=session.mission,
        values=session.values,
        company_name=session.company_name,
        industry=session.industry,
        stage=session.stage,
        team_size=session.team_size,
        selected_track=session.selected_track,
        additional_info=session.additional_info
    )

@router.get("", response_model=List[SessionResponse])
async def list_sessions(
    skip: int = 0,
    limit: int = 20,
    db: AsyncSession = Depends(get_session)
):
    """
    获取会话列表
    """
    result = await db.execute(
        select(SessionModel)
        .order_by(SessionModel.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    sessions = result.scalars().all()
    
    return [
        SessionResponse(
            session_id=s.session_id,
            current_stage=s.current_stage,
            status=s.status,
            created_at=s.created_at
        )
        for s in sessions
    ]
