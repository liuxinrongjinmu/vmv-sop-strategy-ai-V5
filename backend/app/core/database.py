from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings
import os

# 确保数据目录存在
os.makedirs("data", exist_ok=True)

# 创建异步引擎
engine = create_async_engine(
    settings.database_url,
    echo=settings.debug,
    future=True
)

# 创建异步会话工厂
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async_session_factory = async_session

class Base(DeclarativeBase):
    """SQLAlchemy基类"""
    pass

async def init_db():
    """
    初始化数据库
    创建所有表
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_session() -> AsyncSession:
    """
    获取数据库会话
    用于依赖注入
    """
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
