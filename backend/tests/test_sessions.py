"""
测试会话管理API
"""
import pytest
from httpx import AsyncClient

VALID_SESSION_DATA = {
    "vision": "成为行业领导者",
    "mission": "为客户提供优质服务",
    "values": ["创新", "诚信", "卓越"],
    "company_name": "测试公司",
    "industry": "科技",
    "stage": "0-1",
    "team_size": "1-10",
    "selected_track": "人工智能"
}


@pytest.mark.anyio
async def test_create_session(client: AsyncClient):
    """测试创建会话"""
    response = await client.post("/api/sessions", json=VALID_SESSION_DATA)
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert data["current_stage"] == 1
    assert data["status"] == "active"


@pytest.mark.anyio
async def test_create_session_missing_fields(client: AsyncClient):
    """测试缺少必填字段"""
    response = await client.post("/api/sessions", json={"vision": "test"})
    assert response.status_code == 422  # 验证错误


@pytest.mark.anyio
async def test_get_session(client: AsyncClient):
    """测试获取会话"""
    # 先创建
    create_resp = await client.post("/api/sessions", json=VALID_SESSION_DATA)
    session_id = create_resp.json()["session_id"]
    
    # 再获取
    response = await client.get(f"/api/sessions/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert data["company_name"] == "测试公司"


@pytest.mark.anyio
async def test_get_nonexistent_session(client: AsyncClient):
    """测试获取不存在的会话"""
    response = await client.get("/api/sessions/nonexistent-id")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_list_sessions(client: AsyncClient):
    """测试会话列表"""
    # 创建两个会话
    await client.post("/api/sessions", json=VALID_SESSION_DATA)
    await client.post("/api/sessions", json=VALID_SESSION_DATA)
    
    response = await client.get("/api/sessions")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 2


@pytest.mark.anyio
async def test_update_session(client: AsyncClient):
    """测试更新会话"""
    resp = await client.post("/api/sessions", json=VALID_SESSION_DATA)
    session_id = resp.json()["session_id"]

    response = await client.put(f"/api/sessions/{session_id}", json={
        "company_name": "更新后的公司名"
    })
    assert response.status_code == 200
    assert response.json()["company_name"] == "更新后的公司名"


@pytest.mark.anyio
async def test_update_session_not_found(client: AsyncClient):
    """测试更新不存在的会话"""
    response = await client.put("/api/sessions/nonexistent", json={
        "company_name": "更新后的公司名"
    })
    assert response.status_code == 404


@pytest.mark.anyio
async def test_delete_session(client: AsyncClient):
    """测试删除会话"""
    resp = await client.post("/api/sessions", json=VALID_SESSION_DATA)
    session_id = resp.json()["session_id"]

    response = await client.delete(f"/api/sessions/{session_id}")
    assert response.status_code == 200

    # 确认已删除
    response = await client.get(f"/api/sessions/{session_id}")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_delete_session_not_found(client: AsyncClient):
    """测试删除不存在的会话"""
    response = await client.delete("/api/sessions/nonexistent")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_session_detail_contains_all_fields(client: AsyncClient):
    """测试会话详情包含所有字段"""
    resp = await client.post("/api/sessions", json=VALID_SESSION_DATA)
    session_id = resp.json()["session_id"]

    response = await client.get(f"/api/sessions/{session_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["session_id"] == session_id
    assert data["company_name"] == "测试公司"
    assert data["vision"] == "成为行业领导者"
    assert data["mission"] == "为客户提供优质服务"
    assert data["industry"] == "科技"
    assert data["selected_track"] == "人工智能"