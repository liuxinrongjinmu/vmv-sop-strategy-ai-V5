"""
测试安全相关功能
"""
import pytest
from httpx import AsyncClient


@pytest.fixture
def enable_api_key():
    """临时启用API Key验证"""
    from app.config import settings
    original_key = settings.api_key
    settings.api_key = "test-secret-key"
    yield
    settings.api_key = original_key


@pytest.mark.anyio
async def test_api_key_not_required_by_default(client: AsyncClient):
    """测试默认情况下不需要API Key"""
    response = await client.get("/api/sessions")
    assert response.status_code == 200


@pytest.mark.anyio
async def test_api_key_required(client: AsyncClient, enable_api_key):
    """测试API Key验证 - 缺少Key"""
    response = await client.get("/api/sessions")
    assert response.status_code == 401


@pytest.mark.anyio
async def test_api_key_invalid(client: AsyncClient, enable_api_key):
    """测试API Key验证 - 无效Key"""
    response = await client.get(
        "/api/sessions",
        headers={"X-API-Key": "wrong-key"}
    )
    assert response.status_code == 403


@pytest.mark.anyio
async def test_api_key_valid(client: AsyncClient, enable_api_key):
    """测试API Key验证 - 有效Key"""
    response = await client.get(
        "/api/sessions",
        headers={"X-API-Key": "test-secret-key"}
    )
    assert response.status_code == 200


@pytest.mark.anyio
async def test_api_key_protects_chat_send(client: AsyncClient, enable_api_key):
    """测试API Key保护聊天发送端点"""
    response = await client.post("/api/chat/send", json={
        "session_id": "test",
        "content": "hello"
    })
    assert response.status_code == 401


@pytest.mark.anyio
async def test_api_key_protects_report_generate(client: AsyncClient, enable_api_key):
    """测试API Key保护报告生成端点"""
    response = await client.post("/api/report/generate", json={
        "session_id": "test",
        "prediction": "test"
    })
    assert response.status_code == 401


@pytest.mark.anyio
async def test_api_key_protects_session_create(client: AsyncClient, enable_api_key):
    """测试API Key保护会话创建端点"""
    response = await client.post("/api/sessions", json={
        "vision": "test",
        "mission": "test",
        "values": ["test"],
        "company_name": "test",
        "industry": "test",
        "stage": "0-1",
        "selected_track": "test"
    })
    assert response.status_code == 401
