"""
测试对话API端点
"""
import pytest
from httpx import AsyncClient

VALID_SESSION_DATA = {
    "vision": "测试愿景",
    "mission": "测试使命",
    "values": ["价值观1"],
    "company_name": "测试公司",
    "industry": "科技",
    "stage": "0-1",
    "selected_track": "人工智能"
}


@pytest.mark.anyio
async def test_send_message(client: AsyncClient, mock_orchestrator):
    """测试发送消息"""
    # 先创建会话
    resp = await client.post("/api/sessions", json=VALID_SESSION_DATA)
    session_id = resp.json()["session_id"]

    # 发送消息
    response = await client.post("/api/chat/send", json={
        "session_id": session_id,
        "content": "你好"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "assistant"
    assert "content" in data


@pytest.mark.anyio
async def test_send_message_invalid_session(client: AsyncClient):
    """测试发送消息到不存在的会话"""
    response = await client.post("/api/chat/send", json={
        "session_id": "nonexistent",
        "content": "你好"
    })
    assert response.status_code == 404


@pytest.mark.anyio
async def test_send_message_missing_content(client: AsyncClient):
    """测试发送消息缺少内容字段"""
    response = await client.post("/api/chat/send", json={
        "session_id": "some-session"
    })
    assert response.status_code == 422


@pytest.mark.anyio
async def test_get_chat_history(client: AsyncClient):
    """测试获取对话历史"""
    # 先创建会话
    resp = await client.post("/api/sessions", json=VALID_SESSION_DATA)
    session_id = resp.json()["session_id"]

    response = await client.get(f"/api/chat/history/{session_id}")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.anyio
async def test_get_chat_history_invalid_session(client: AsyncClient):
    """测试获取不存在会话的对话历史"""
    response = await client.get("/api/chat/history/nonexistent")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_upload_file_invalid_type(client: AsyncClient):
    """测试上传不支持的文件类型"""
    response = await client.post(
        "/api/chat/upload",
        files={"file": ("test.exe", b"fake content", "application/octet-stream")}
    )
    assert response.status_code == 400


@pytest.mark.anyio
async def test_upload_file_empty(client: AsyncClient):
    """测试上传空文件"""
    response = await client.post(
        "/api/chat/upload",
        files={"file": ("test.txt", b"", "text/plain")}
    )
    assert response.status_code == 400


@pytest.mark.anyio
async def test_upload_file_valid_txt(client: AsyncClient):
    """测试上传有效的TXT文件"""
    response = await client.post(
        "/api/chat/upload",
        files={"file": ("test.txt", b"Hello World", "text/plain")}
    )
    assert response.status_code == 200
    data = response.json()
    assert "file_id" in data
    assert data["filename"] == "test.txt"
