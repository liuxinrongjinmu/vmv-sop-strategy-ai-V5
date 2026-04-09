from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from urllib.parse import quote
import asyncio
from datetime import datetime

from app.core.database import get_session
from app.models.models import Session as SessionModel, Report, Message
from app.schemas.schemas import ReportCreate, ReportResponse
from app.agents.ten_year import ten_year_agent
from app.services.report_export import report_export_service

router = APIRouter(prefix="/api/report", tags=["report"])

report_tasks = {}

@router.post("/generate")
async def generate_report(
    data: ReportCreate,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_session)
):
    """
    异步生成分析报告
    立即返回任务ID，后台执行生成逻辑
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
    
    task_id = f"report_{session.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    
    report_tasks[task_id] = {
        "status": "processing",
        "progress": 0,
        "message": "正在生成报告...",
        "session_db_id": session.id,
        "report_type": data.report_type,
        "created_at": datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')
    }
    
    background_tasks.add_task(
        _generate_report_background,
        task_id=task_id,
        prediction=data.prediction,
        context=context,
        session_db_id=session.id,
        report_type=data.report_type
    )
    
    return {"task_id": task_id, "status": "processing", "message": "报告生成已开始，请稍候..."}


async def _generate_report_background(
    task_id: str,
    prediction: str,
    context: dict,
    session_db_id: int,
    report_type: str
):
    """
    后台任务：生成报告
    """
    try:
        report_tasks[task_id]["status"] = "processing"
        report_tasks[task_id]["progress"] = 10
        report_tasks[task_id]["message"] = "正在提取关键洞察..."
        
        report_data = await ten_year_agent.analyze(prediction, context)
        
        report_tasks[task_id]["progress"] = 90
        report_tasks[task_id]["message"] = "正在保存报告..."
        
        from app.core.database import async_session_factory
        
        async with async_session_factory() as db:
            report = Report(
                session_id=session_db_id,
                report_type=report_type,
                title=report_data["title"],
                content=report_data["content"],
                sources=report_data["sources"]
            )
            db.add(report)
            await db.commit()
            await db.refresh(report)
            
            report_tasks[task_id]["status"] = "completed"
            report_tasks[task_id]["progress"] = 100
            report_tasks[task_id]["message"] = "报告生成完成"
            report_tasks[task_id]["report_id"] = report.id
            report_tasks[task_id]["title"] = report.title
            report_tasks[task_id]["content"] = report.content
            report_tasks[task_id]["sources"] = report.sources
            report_tasks[task_id]["created_at"] = report.created_at.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    except Exception as e:
        print(f"[ReportTask] 报告生成失败: {e}")
        report_tasks[task_id]["status"] = "failed"
        report_tasks[task_id]["progress"] = 0
        report_tasks[task_id]["message"] = f"报告生成失败: {str(e)}"


@router.get("/task/{task_id}")
async def get_task_status(task_id: str):
    """
    查询报告生成任务状态
    """
    if task_id not in report_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    task = report_tasks[task_id]
    
    if task["status"] == "completed":
        return {
            "status": "completed",
            "progress": 100,
            "message": "报告生成完成",
            "report": {
                "id": task["report_id"],
                "title": task["title"],
                "content": task["content"],
                "sources": task["sources"],
                "created_at": task["created_at"]
            }
        }
    elif task["status"] == "failed":
        return {
            "status": "failed",
            "progress": 0,
            "message": task["message"]
        }
    else:
        return {
            "status": "processing",
            "progress": task["progress"],
            "message": task["message"]
        }


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
    result = await db.execute(
        select(Report).where(Report.id == report_id)
    )
    report = result.scalar_one_or_none()
    
    if not report:
        raise HTTPException(status_code=404, detail="报告不存在")
    
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
    
    encoded_filename = quote(filename)
    
    return Response(
        content=content,
        media_type=media_type,
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{encoded_filename}"
        }
    )
