from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from urllib.parse import quote

from app.core.database import get_session
from app.models.models import Session as SessionModel, Report, Message
from app.schemas.schemas import ReportCreate, ReportResponse
from app.agents.ten_year import ten_year_agent
from app.services.report_export import report_export_service

router = APIRouter(prefix="/api/report", tags=["report"])

@router.post("/generate", response_model=ReportResponse)
async def generate_report(
    data: ReportCreate,
    db: AsyncSession = Depends(get_session)
):
    """
    生成分析报告
    调用十年战略Agent进行分析
    """
    result = await db.execute(
        select(SessionModel).where(SessionModel.session_id == data.session_id)
    )
    session = result.scalar_one_or_none()
    
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    
    session_info = {
        "company_name": session.company_name,
        "industry": session.industry,
        "stage": session.stage,
        "team_size": session.team_size,
        "selected_track": session.selected_track,
        "vision": session.vision,
        "mission": session.mission,
        "values": session.values,
        "additional_info": session.additional_info
    }
    
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session.id)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()
    
    chat_history = []
    uploaded_files = []
    
    for msg in messages:
        if msg.role == "user":
            chat_history.append({
                "role": "user",
                "content": msg.content,
                "stage": msg.stage
            })
        elif msg.role == "assistant":
            chat_history.append({
                "role": "assistant",
                "content": msg.content,
                "stage": msg.stage
            })
        elif msg.role == "system" and msg.file_content:
            uploaded_files.append({
                "filename": msg.file_name,
                "content": msg.file_content[:3000]
            })
    
    context = {
        "session_info": session_info,
        "chat_history": chat_history,
        "uploaded_files": uploaded_files
    }
    
    report_data = await ten_year_agent.analyze(data.prediction, context)
    
    report = Report(
        session_id=session.id,
        report_type=data.report_type,
        title=report_data["title"],
        content=report_data["content"],
        sources=report_data["sources"]
    )
    db.add(report)
    await db.commit()
    await db.refresh(report)
    
    return ReportResponse(
        id=report.id,
        title=report.title,
        content=report.content,
        sources=report.sources,
        created_at=report.created_at
    )

@router.get("/{report_id}", response_model=ReportResponse)
async def get_report(
    report_id: int,
    db: AsyncSession = Depends(get_session)
):
    """
    获取报告详情
    """
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    return ReportResponse(
        id=report.id,
        title=report.title,
        content=report.content,
        sources=report.sources,
        created_at=report.created_at
    )

@router.get("/{report_id}/export")
async def export_report(
    report_id: int,
    format: str = "md",
    db: AsyncSession = Depends(get_session)
):
    """
    导出报告
    支持md、pdf、docx格式
    """
    # 获取报告
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
    # 根据格式导出
    if format == "md":
        content, filename = report_export_service.export_markdown(
            report.content, report.title
        )
        media_type = "text/markdown"
    elif format == "pdf":
        content, filename = report_export_service.export_pdf(
            report.content, report.title
        )
        media_type = "application/pdf"
    elif format == "docx":
        content, filename = report_export_service.export_docx(
            report.content, report.title
        )
        media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    else:
        raise HTTPException(status_code=400, detail=f"不支持的导出格式: {format}")
    
    # 对文件名进行URL编码，支持中文
    encoded_filename = quote(filename)
    
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )
