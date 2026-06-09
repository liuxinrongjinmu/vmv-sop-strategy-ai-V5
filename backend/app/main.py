from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.database import init_db
from app.api import sessions, chat, report
from app.config import settings

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    启动时初始化数据库
    """
    await init_db()
    yield

app = FastAPI(
    title="VMV-SOP战略咨询系统API",
    description="基于From VMV to SOP理论的AI驱动战略咨询系统",
    version="1.0.0",
    lifespan=lifespan
)

# 配置CORS：从环境变量读取允许的origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(sessions.router)
app.include_router(chat.router)
app.include_router(report.router)

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "VMV-SOP战略咨询系统API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}
