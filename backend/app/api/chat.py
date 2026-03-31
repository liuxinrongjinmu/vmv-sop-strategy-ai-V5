from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid
import logging

from app.core.database import get_session
from app.models.models import Session as SessionModel, Message
from app.schemas.schemas import MessageCreate, MessageResponse, FileUploadResponse
from app.agents.orchestrator import orchestrator_agent
from app.services.file_parser import file_parser

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = logging.getLogger(__name__)

@router.post("/send", response_model=MessageResponse)
async def send_message(
    data: MessageCreate,
    db: AsyncSession = Depends(get_session)
):
    """
    发送消息
    处理用户输入，调用Agent生成响应
    """
    result = await db.execute(
        select(SessionModel).where(SessionModel.session_id == data.session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    user_message = Message(
        session_id=session.id,
        role="user",
        content=data.content,
        stage=session.current_stage
    )
    db.add(user_message)
    await db.commit()
    
    file_messages = await db.execute(
        select(Message)
        .where(Message.session_id == session.id)
        .where(Message.role == "system")
        .where(Message.file_content.isnot(None))
        .order_by(Message.created_at.desc())
        .limit(3)
    )
    uploaded_files = []
    for fm in file_messages.scalars().all():
        if fm.file_content:
            uploaded_files.append({
                "filename": fm.file_name,
                "content": fm.file_content
            })
    
    session_info = {
        "company_name": session.company_name,
        "industry": session.industry,
        "stage": session.stage,
        "selected_track": session.selected_track,
        "vision": session.vision,
        "mission": session.mission,
        "values": session.values,
        "additional_info": session.additional_info
    }
    
    agent_result = await orchestrator_agent.process_message(
        data.content,
        session_info,
        session.current_stage,
        uploaded_files
    )
    
    if agent_result.get("stage") and agent_result["stage"] != session.current_stage:
        session.current_stage = agent_result["stage"]
        await db.commit()
    
    ai_message = Message(
        session_id=session.id,
        role="assistant",
        content=agent_result["content"],
        stage=session.current_stage,
        extra_data={"type": agent_result.get("type"), "sources": agent_result.get("sources")}
    )
    db.add(ai_message)
    await db.commit()
    await db.refresh(ai_message)
    
    return MessageResponse(
        id=ai_message.id,
        role=ai_message.role,
        content=ai_message.content,
        stage=ai_message.stage,
        created_at=ai_message.created_at
    )

@router.get("/history/{session_id}", response_model=List[MessageResponse])
async def get_chat_history(
    session_id: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_session)
):
    """
    获取对话历史
    """
    result = await db.execute(
        select(SessionModel).where(SessionModel.session_id == session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session.id)
        .order_by(Message.created_at.asc())
        .limit(limit)
    )
    messages = result.scalars().all()
    
    return [
        MessageResponse(
            id=m.id,
            role=m.role,
            content=m.content,
            stage=m.stage,
            created_at=m.created_at
        )
        for m in messages
    ]

@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    session_id: str = None,
    db: AsyncSession = Depends(get_session)
):
    """
    上传文件
    支持PDF、Word格式
    """
    logger.info(f"收到文件上传请求: filename={file.filename}, session_id={session_id}")
    
    allowed_types = [".pdf", ".docx", ".doc", ".txt", ".md"]
    file_ext = "." + file.filename.split(".")[-1].lower()
    
    if file_ext not in allowed_types:
        logger.warning(f"不支持的文件类型: {file_ext}")
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file_ext}")
    
    try:
        file_content = await file.read()
        logger.info(f"文件大小: {len(file_content)} bytes")
        
        content = await file_parser.parse_file(file_content, file.filename)
        logger.info(f"文件解析成功，提取内容约{len(content)}字符")
        
        file_id = str(uuid.uuid4())
        
        if session_id:
            result = await db.execute(
                select(SessionModel).where(SessionModel.session_id == session_id)
            )
            session = result.scalar_one_or_none()
            
            if session:
                file_message = Message(
                    session_id=session.id,
                    role="system",
                    content=f"[文件上传] {file.filename}",
                    stage=session.current_stage,
                    file_name=file.filename,
                    file_content=content
                )
                db.add(file_message)
                await db.commit()
                logger.info(f"文件内容已存储到数据库: {file.filename}")
        
        return FileUploadResponse(
            file_id=file_id,
            filename=file.filename,
            content=content[:2000],
            message=f"文件解析成功，提取内容约{len(content)}字符"
        )
    except Exception as e:
        logger.error(f"文件解析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件解析失败: {str(e)}")
