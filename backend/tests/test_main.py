"""
测试主应用基础功能
"""
import pytest
from httpx import AsyncClient


@pytest.mark.anyio
async def test_root(client: AsyncClient):
    """测试根路径"""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "VMV-SOP战略咨询系统API"
    assert data["version"] == "1.0.0"


@pytest.mark.anyio
async def test_health_check(client: AsyncClient):
    """测试健康检查"""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "checks" in data
    assert "database" in data["checks"]