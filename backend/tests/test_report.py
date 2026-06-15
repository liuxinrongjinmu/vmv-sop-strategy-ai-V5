"""
测试报告API端点
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
async def test_generate_report(client: AsyncClient, mock_ten_year_agent, mock_five_year_agent, mock_three_year_agent, mock_one_year_agent):
    """测试报告生成"""
    # 先创建会话
    resp = await client.post("/api/sessions", json=VALID_SESSION_DATA)
    session_id = resp.json()["session_id"]

    response = await client.post("/api/report/generate", json={
        "session_id": session_id,
        "prediction": "AI行业将持续增长",
        "report_type": "ten_year"
    })
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
    assert data["status"] == "processing"


@pytest.mark.anyio
async def test_generate_report_invalid_session(client: AsyncClient):
    """测试为不存在的会话生成报告"""
    response = await client.post("/api/report/generate", json={
        "session_id": "nonexistent",
        "prediction": "测试预判"
    })
    assert response.status_code == 404


@pytest.mark.anyio
async def test_generate_report_missing_fields(client: AsyncClient):
    """测试生成报告缺少必填字段"""
    response = await client.post("/api/report/generate", json={
        "session_id": "some-session"
    })
    assert response.status_code == 422


@pytest.mark.anyio
async def test_report_task_not_found(client: AsyncClient):
    """测试查询不存在的报告任务"""
    response = await client.get("/api/report/task/nonexistent")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_report_not_found(client: AsyncClient):
    """测试获取不存在的报告"""
    response = await client.get("/api/report/99999")
    assert response.status_code == 404


@pytest.mark.anyio
async def test_generate_five_year_report(client: AsyncClient, mock_five_year_agent, mock_ten_year_agent, mock_three_year_agent, mock_one_year_agent):
    """测试生成五年分析报告"""
    resp = await client.post("/api/sessions", json=VALID_SESSION_DATA)
    session_id = resp.json()["session_id"]

    response = await client.post("/api/report/generate", json={
        "session_id": session_id,
        "prediction": "五年关键驱动因素分析",
        "report_type": "five_year"
    })
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data


@pytest.mark.anyio
async def test_generate_three_year_report(client: AsyncClient, mock_three_year_agent, mock_ten_year_agent, mock_five_year_agent, mock_one_year_agent):
    """测试生成三年目标报告"""
    resp = await client.post("/api/sessions", json=VALID_SESSION_DATA)
    session_id = resp.json()["session_id"]

    response = await client.post("/api/report/generate", json={
        "session_id": session_id,
        "prediction": "三年阶段性目标",
        "report_type": "three_year"
    })
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data


@pytest.mark.anyio
async def test_generate_one_year_report(client: AsyncClient, mock_one_year_agent, mock_ten_year_agent, mock_five_year_agent, mock_three_year_agent):
    """测试生成一年任务分解报告"""
    resp = await client.post("/api/sessions", json=VALID_SESSION_DATA)
    session_id = resp.json()["session_id"]

    response = await client.post("/api/report/generate", json={
        "session_id": session_id,
        "prediction": "一年任务分解",
        "report_type": "one_year"
    })
    assert response.status_code == 200
    data = response.json()
    assert "task_id" in data
