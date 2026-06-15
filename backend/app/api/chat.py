from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid
import json
import logging

from app.core.database import get_session
from app.models.models import Session as SessionModel, Message
from app.schemas.schemas import MessageCreate, MessageResponse, FileUploadResponse
from app.agents.orchestrator import orchestrator_agent
from app.services.file_parser import file_parser
from app.core.security import limiter, verify_api_key

router = APIRouter(prefix="/api/chat", tags=["chat"])
logger = logging.getLogger(__name__)

# 文件上传限制
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10MB


async def _build_chat_context(session: SessionModel, db: AsyncSession) -> tuple:
    """
    构建对话上下文（公共方法）
    返回 (uploaded_files, session_info, chat_history)
    """
    # 获取文件上下文
    file_result = await db.execute(
        select(Message)
        .where(Message.session_id == session.id)
        .where(Message.role == "system")
        .where(Message.file_content.isnot(None))
        .order_by(Message.created_at.desc())
        .limit(3)
    )
    uploaded_files = []
    for fm in file_result.scalars().all():
        if fm.file_content:
            uploaded_files.append({"filename": fm.file_name, "content": fm.file_content})
    
    # 构建session_info
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
    
    # 获取历史消息
    chat_history_result = await db.execute(
        select(Message)
        .where(Message.session_id == session.id)
        .where(Message.role.in_(["user", "assistant"]))
        .order_by(Message.created_at.desc())
        .limit(20)
    )
    chat_history = []
    for msg in reversed(list(chat_history_result.scalars().all())):
        extra = msg.extra_data or {}
        if extra.get("type") == "report":
            chat_history.append({"role": "assistant", "content": f"[十年战略分析报告]\n{msg.content[:8000]}"})
        else:
            chat_history.append({"role": msg.role, "content": msg.content[:2000]})
    
    return uploaded_files, session_info, chat_history


@router.post("/send", response_model=MessageResponse, dependencies=[Depends(verify_api_key)])
@limiter.limit("30/minute")
async def send_message(
    request: Request,
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
    
    uploaded_files, session_info, chat_history = await _build_chat_context(session, db)
    
    agent_result = await orchestrator_agent.process_message(
        data.content,
        session_info,
        session.current_stage,
        uploaded_files,
        chat_history
    )
    
    if agent_result.get("stage") and agent_result["stage"] != session.current_stage:
        session.current_stage = agent_result["stage"]
        await db.commit()
    
    extra_data = {
        "type": agent_result.get("type"),
        "sources": agent_result.get("sources")
    }
    
    ai_message = Message(
        session_id=session.id,
        role="assistant",
        content=agent_result["content"],
        stage=session.current_stage,
        extra_data=extra_data
    )
    db.add(ai_message)
    await db.commit()
    await db.refresh(ai_message)
    
    return MessageResponse(
        id=ai_message.id,
        role=ai_message.role,
        content=ai_message.content,
        stage=ai_message.stage,
        created_at=ai_message.created_at,
        metadata=extra_data
    )

@router.post("/send/stream", dependencies=[Depends(verify_api_key)])
@limiter.limit("30/minute")
async def send_message_stream(
    request: Request,
    data: MessageCreate,
    db: AsyncSession = Depends(get_session)
):
    """
    发送消息（SSE流式响应）
    实时逐字返回Agent生成的内容
    """
    result = await db.execute(
        select(SessionModel).where(SessionModel.session_id == data.session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    # 保存用户消息
    user_message = Message(
        session_id=session.id,
        role="user",
        content=data.content,
        stage=session.current_stage
    )
    db.add(user_message)
    await db.commit()
    
    # 构建对话上下文
    uploaded_files, session_info, chat_history = await _build_chat_context(session, db)
    
    # 保存session引用和db引用供event_generator使用
    session_ref = session
    db_ref = db
    
    async def event_generator():
        """SSE事件生成器（真流式）"""
        full_content = ""  # 累积完整文本用于保存到数据库
        try:
            # 发送阶段信息
            yield f"data: {json.dumps({'type': 'stage', 'stage': session_ref.current_stage})}\n\n"

            async for event in orchestrator_agent.process_message_stream(
                data.content,
                session_info,
                session_ref.current_stage,
                uploaded_files,
                chat_history
            ):
                event_type = event.get("type")

                if event_type in ("report", "stage_transition"):
                    # report和stage_transition类型直接转发
                    new_stage = event.get("stage")
                    if new_stage and new_stage != session_ref.current_stage:
                        session_ref.current_stage = new_stage
                        await db_ref.commit()
                    full_content = event.get("content", "")
                    yield f"data: {json.dumps(event)}\n\n"
                    yield "data: [DONE]\n\n"

                elif event_type == "text":
                    # 逐token转发
                    token = event.get("content", "")
                    full_content += token
                    yield f"data: {json.dumps(event)}\n\n"

                elif event_type == "meta":
                    # meta事件在流结束时发送
                    new_stage = event.get("stage")
                    if new_stage and new_stage != session_ref.current_stage:
                        session_ref.current_stage = new_stage
                        await db_ref.commit()
                    yield f"data: {json.dumps(event)}\n\n"
                    yield "data: [DONE]\n\n"

            # 将AI响应保存到数据库
            extra_data = {
                "type": "chat",
                "sources": []
            }
            ai_message = Message(
                session_id=session_ref.id,
                role="assistant",
                content=full_content,
                stage=session_ref.current_stage,
                extra_data=extra_data
            )
            db_ref.add(ai_message)
            await db_ref.commit()

        except Exception as e:
            logger.error(f"SSE流式响应异常: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'content': '内容生成失败，请重试'})}\n\n"
            yield "data: [DONE]\n\n"
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )

@router.get("/history/{session_id}", response_model=List[MessageResponse], dependencies=[Depends(verify_api_key)])
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
            created_at=m.created_at,
            metadata=m.extra_data
        )
        for m in messages
    ]

@router.post("/upload", response_model=FileUploadResponse, dependencies=[Depends(verify_api_key)])
@limiter.limit("10/minute")
async def upload_file(
    request: Request,
    file: UploadFile = File(...),
    session_id: str = None,
    db: AsyncSession = Depends(get_session)
):
    """
    上传文件
    支持PDF、Word、TXT、MD格式，最大10MB
    """
    logger.info(f"收到文件上传请求: filename={file.filename}, session_id={session_id}")
    
    # 文件大小校验
    file_content = await file.read()
    file_size = len(file_content)
    
    if file_size > MAX_UPLOAD_SIZE:
        logger.warning(f"文件过大: {file.filename} ({file_size} bytes)")
        raise HTTPException(
            status_code=413, 
            detail=f"文件过大({file_size / 1024 / 1024:.1f}MB)，最大允许{MAX_UPLOAD_SIZE / 1024 / 1024:.0f}MB"
        )
    if file_size == 0:
        raise HTTPException(status_code=400, detail="文件内容为空")
    
    # 文件类型校验
    allowed_types = [".pdf", ".docx", ".doc", ".txt", ".md"]
    file_ext = "." + file.filename.split(".")[-1].lower() if "." in file.filename else ""
    
    if file_ext not in allowed_types:
        logger.warning(f"不支持的文件类型: {file_ext}")
        raise HTTPException(status_code=400, detail=f"不支持的文件类型: {file_ext}")
    
    try:
        logger.info(f"文件大小: {file_size} bytes")
        
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
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"文件解析失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"文件解析失败: {str(e)}")
