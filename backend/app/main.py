from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import os
import shutil
from logging.handlers import RotatingFileHandler

from app.core.database import init_db, get_session
from app.core.security import limiter, verify_api_key
from app.api import sessions, chat, report
from app.config import settings

# 确保日志目录存在
os.makedirs("logs", exist_ok=True)

# 配置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        # 控制台输出
        logging.StreamHandler(),
        # 文件轮转输出（每个文件最大10MB，保留5个备份）
        RotatingFileHandler(
            "logs/app.log",
            maxBytes=10 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8"
        )
    ]
)
logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    """创建FastAPI应用实例"""
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """
        应用生命周期管理
        启动时初始化数据库
        """
        logger.info("正在初始化数据库...")
        await init_db()
        logger.info("数据库初始化完成")
        yield
    
    app = FastAPI(
        title="VMV-SOP战略咨询系统API",
        description="基于From VMV to SOP理论的AI驱动战略咨询系统",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None
    )
    
    # 配置CORS：从环境变量读取允许的origins
    cors_origins = settings.get_cors_origins()
    logger.info(f"CORS origins: {cors_origins}")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )

    # 安全响应头中间件
    @app.middleware("http")
    async def add_security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; connect-src 'self' https:;"
        return response
    
    # 注册限流异常处理
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    
    # 注册统一异常处理
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.warning(f"HTTP异常: {exc.status_code} - {exc.detail} - {request.url}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"未捕获异常: {type(exc).__name__} - {str(exc)} - {request.url}", exc_info=True)
        detail = str(exc) if settings.debug else "服务器内部错误，请稍后重试"
        return JSONResponse(
            status_code=500,
            content={"detail": detail}
        )
    
    # 注册路由（带认证依赖注入到需要保护的路由组）
    app.include_router(sessions.router, dependencies=[])
    app.include_router(chat.router, dependencies=[])
    app.include_router(report.router, dependencies=[])
    
    @app.get("/")
    async def root():
        """根路径"""
        return {
            "message": "VMV-SOP战略咨询系统API",
            "version": "1.0.0",
            "docs": "/docs" if settings.debug else None
        }
    
    @app.get("/health")
    async def health_check(db: AsyncSession = Depends(get_session)):
        """健康检查 - 检查数据库连接、磁盘空间和LLM配置"""
        checks = {"status": "healthy", "checks": {}}

        # 检查数据库连接
        try:
            await db.execute(text("SELECT 1"))
            checks["checks"]["database"] = "ok"
        except Exception as e:
            checks["checks"]["database"] = f"error: {str(e)}"
            checks["status"] = "unhealthy"

        # 检查磁盘空间
        try:
            usage = shutil.disk_usage("./")
            free_percent = (usage.free / usage.total) * 100
            if free_percent < 10:
                checks["checks"]["disk"] = f"warning: only {free_percent:.1f}% free"
                checks["status"] = "degraded"
            else:
                checks["checks"]["disk"] = f"ok ({free_percent:.1f}% free)"
        except Exception as e:
            checks["checks"]["disk"] = f"error: {str(e)}"

        # 检查LLM API Key配置
        checks["checks"]["llm_configured"] = bool(settings.zhipu_api_key or settings.qwen_api_key)

        return checks
    
    return app


app = create_app()