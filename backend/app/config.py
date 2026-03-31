from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    """
    应用配置类
    从.env文件加载配置
    """
    # 大模型API配置
    zhipu_api_key: str = ""
    qwen_api_key: str = ""
    
    # 搜索API配置
    tavily_api_key: str = ""
    
    # 模型配置
    llm_primary_provider: str = "zhipu"
    llm_fallback_provider: str = "qwen"
    
    # 数据库配置
    database_url: str = "sqlite+aiosqlite:///./data/vmv_sop.db"
    
    # 服务配置
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    debug: bool = True
    
    class Config:
        env_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
        case_sensitive = False

settings = Settings()
