from pydantic_settings import BaseSettings
from typing import Optional, List
import os

class Settings(BaseSettings):
    """
    应用配置类
    从.env文件加载配置
    """
    # 安全配置
    api_key: str = ""
    
    # 大模型API配置
    zhipu_api_key: str = ""
    qwen_api_key: str = ""
    
    # 搜索API配置
    tavily_api_key: str = ""
    
    # 模型配置
    llm_primary_provider: str = "zhipu"
    llm_fallback_provider: str = "qwen"
    
    # 数据库配置
    # SQLite(开发默认): sqlite+aiosqlite:///./data/vmv_sop.db
    # PostgreSQL(生产): postgresql+asyncpg://user:password@localhost:5432/vmv_sop
    database_url: str = "sqlite+aiosqlite:///./data/vmv_sop.db"

    @property
    def is_postgresql(self) -> bool:
        """判断是否使用PostgreSQL数据库"""
        return "postgresql" in self.database_url
    
    # 服务配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = False
    
    # CORS配置：逗号分隔的允许origins列表，留空则仅允许localhost
    cors_origins: str = ""
    
    # 限流配置
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 30
    rate_limit_report_per_minute: int = 5
    
    def get_cors_origins(self) -> List[str]:
        """
        获取CORS允许的origins列表
        生产环境不允许通配符，默认仅允许localhost
        """
        if not self.cors_origins:
            # 默认仅允许本地开发
            return [
                "http://localhost:3000",
                "http://localhost:3001",
                "http://localhost:5173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:3001",
                "http://127.0.0.1:5173"
            ]
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
    
    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        case_sensitive = False

settings = Settings()
