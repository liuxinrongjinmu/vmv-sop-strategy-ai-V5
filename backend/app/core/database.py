from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings
import os
import logging

logger = logging.getLogger(__name__)

# 根据数据库类型创建引擎
engine_kwargs = {
    "echo": settings.debug,
    "future": True,
}

if settings.is_postgresql:
    # PostgreSQL 连接池配置
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_recycle": 3600,
        "pool_pre_ping": True,
    })
else:
    # SQLite 配置
    db_path = settings.database_url.split("///")[-1]
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)
    engine_kwargs["connect_args"] = {"check_same_thread": False}

engine = create_async_engine(settings.database_url, **engine_kwargs)

async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


class Base(DeclarativeBase):
    """SQLAlchemy基类"""
    pass


async def init_db():
    """
    初始化数据库
    创建所有表
    必须在导入所有模型后调用
    """
    # 显式导入所有模型，确保它们注册到Base.metadata
    from app.models.models import Session, Message, Report, ReportTask  # noqa: F401
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info(f"Database initialized: {'PostgreSQL' if settings.is_postgresql else 'SQLite'}")


async def get_db():
    """
    获取数据库会话
    用于依赖注入
    """
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


# 保持向后兼容的别名
get_session = get_db
