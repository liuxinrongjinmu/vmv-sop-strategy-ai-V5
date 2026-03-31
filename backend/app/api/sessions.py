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
    vision: str = Form(...),
    mission: str = Form(...),
    values: str = Form(...),
    company_name: str = Form(...),
    industry: str = Form(...),
    stage: str = Form(...),
    team_size: str = Form(...),
    selected_track: str = Form(...),
    additional_info: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    db: AsyncSession = Depends(get_session)
):
    """
    创建新会话
    接收VMV和基本信息，初始化会话状态
    支持文件上传并解析文件内容
    """
    logger.info(f"收到创建会话请求: company_name={company_name}, industry={industry}")
    
    # 解析values
    try:
        parsed_values = json.loads(values)
        logger.info(f"解析values成功: {parsed_values}")
    except json.JSONDecodeError:
        logger.warning(f"解析values失败，使用空列表")
        parsed_values = []
    
    # 解析文件内容
    file_contents = []
    if files:
        parser = FileParser()
        for file in files:
            try:
                content = await file.read()
                file_content = await parser.parse_file(content, file.filename)
                file_contents.append(f"文件: {file.filename}\n{file_content}")
            except Exception as e:
                print(f"解析文件 {file.filename} 失败: {e}")
                file_contents.append(f"文件: {file.filename}\n解析失败: {str(e)}")
    
    # 合并附加信息和文件内容
    combined_info = additional_info or ""
    if file_contents:
        combined_info += "\n\n" + "\n\n".join(file_contents)
    
    session = SessionModel(
        vision=vision,
        mission=mission,
        values=parsed_values,
        company_name=company_name,
        industry=industry,
        stage=stage,
        team_size=team_size,
        selected_track=selected_track,
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
