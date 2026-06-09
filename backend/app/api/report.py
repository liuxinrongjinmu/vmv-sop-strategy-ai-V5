from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from urllib.parse import quote
import asyncio
from datetime import datetime, timezone
import logging

from app.core.database import get_session
from app.models.models import Session as SessionModel, Report, ReportTask, Message
from app.schemas.schemas import ReportCreate, ReportResponse
from app.agents.ten_year import ten_year_agent
from app.services.report_export import report_export_service

router = APIRouter(prefix="/api/report", tags=["report"])
logger = logging.getLogger(__name__)


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
    
    task_id = f"report_{session.id}_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    
    # 持久化任务记录到数据库
    report_task = ReportTask(
        task_id=task_id,
        session_db_id=session.id,
        report_type=data.report_type,
        status="processing",
        progress=0,
        message="正在生成报告..."
    )
    db.add(report_task)
    await db.commit()
    
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
    使用数据库持久化任务状态
    """
    from app.core.database import async_session_factory
    
    async with async_session_factory() as db:
        try:
            # 更新任务状态
            result = await db.execute(
                select(ReportTask).where(ReportTask.task_id == task_id)
            )
            task = result.scalar_one_or_none()
            if task:
                task.status = "processing"
                task.progress = 10
                task.message = "正在提取关键洞察..."
                await db.commit()
            
            # 执行分析
            report_data = await ten_year_agent.analyze(prediction, context)
            
            # 保存报告
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
            
            # 更新任务状态为完成
            if task:
                task.status = "completed"
                task.progress = 100
                task.message = "报告生成完成"
                task.report_id = report.id
                task.title = report.title
                task.content = report.content
                task.sources = report.sources
                await db.commit()
            
            logger.info(f"报告生成完成: task_id={task_id}, report_id={report.id}")
        
        except Exception as e:
            logger.error(f"报告生成失败: task_id={task_id}, error={e}")
            
            # 更新任务状态为失败
            result = await db.execute(
                select(ReportTask).where(ReportTask.task_id == task_id)
            )
            task = result.scalar_one_or_none()
            if task:
                task.status = "failed"
                task.progress = 0
                task.message = f"报告生成失败: {str(e)}"
                await db.commit()


@router.get("/task/{task_id}")
async def get_task_status(
    task_id: str,
    db: AsyncSession = Depends(get_session)
):
    """
    查询报告生成任务状态
    从数据库读取，服务重启后仍可查询
    """
    result = await db.execute(
        select(ReportTask).where(ReportTask.task_id == task_id)
    )
    task = result.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    if task.status == "completed":
        return {
            "status": "completed",
            "progress": 100,
            "message": "报告生成完成",
            "report": {
                "id": task.report_id,
                "title": task.title,
                "content": task.content,
                "sources": task.sources,
                "created_at": task.created_at.strftime('%Y-%m-%dT%H:%M:%SZ') if task.created_at else None
            }
        }
    elif task.status == "failed":
        return {
            "status": "failed",
            "progress": 0,
            "message": task.message
        }
    else:
        return {
            "status": "processing",
            "progress": task.progress,
            "message": task.message
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
