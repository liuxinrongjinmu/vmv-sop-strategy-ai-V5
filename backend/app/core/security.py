"""
安全模块：API Key认证 + 请求限流
独立模块，避免循环导入
"""
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.config import settings
import secrets
import logging

logger = logging.getLogger(__name__)

# 全局限流器
limiter = Limiter(key_func=get_remote_address, default_limits=[])

# API Key 认证
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def verify_api_key(api_key: str = Depends(api_key_header)):
    """
    验证API Key
    如果未配置API_KEY则跳过验证（开发模式）
    """
    if not settings.api_key:
        return True
    if api_key is None:
        raise HTTPException(status_code=401, detail="缺少API Key，请在Header中提供 X-API-Key")
    if not secrets.compare_digest(api_key, settings.api_key):
        raise HTTPException(status_code=403, detail="API Key无效")
    return True