"""
测试配置和共享fixtures
"""
import pytest
import os
import sys

# 确保backend在Python路径中
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from unittest.mock import AsyncMock, patch
from httpx import AsyncClient, ASGITransport
from app.main import create_app
from app.core.database import init_db, Base, engine


@pytest.fixture(scope="session")
def anyio_backend():
    """anyio后端"""
    return "asyncio"


@pytest.fixture(autouse=True)
def _setup_env():
    """
    自动设置测试环境变量
    """
    os.environ["DEBUG"] = "true"
    os.environ["API_KEY"] = ""
    os.environ["ZHIPU_API_KEY"] = "test_key"
    os.environ["QWEN_API_KEY"] = ""
    os.environ["TAVILY_API_KEY"] = ""
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///./data/test.db"


@pytest.fixture
async def app():
    """创建测试用FastAPI应用"""
    app = create_app()
    # 测试模式下确保数据库已初始化
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield app


@pytest.fixture
async def client(app):
    """创建测试HTTP客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture(autouse=True)
def _disable_rate_limit():
    """禁用限流，避免测试中因请求频率过高被429"""
    from app.core.security import limiter
    # 每次测试前重置限流器存储
    limiter.reset()
    yield


@pytest.fixture
def mock_llm_service():
    """Mock LLM服务，避免真实API调用"""
    with patch('app.services.llm.llm_service') as mock:
        mock.generate = AsyncMock(return_value="这是模拟的AI响应内容")
        # 模拟流式生成
        async def fake_stream(*args, **kwargs):
            for token in ["这是", "模拟", "的流式", "响应"]:
                yield token
        mock.generate_stream = fake_stream
        yield mock


@pytest.fixture
def mock_search_service():
    """Mock搜索服务"""
    with patch('app.services.search.search_service') as mock:
        mock.search = AsyncMock(return_value=[
            {"title": "测试结果", "link": "https://example.com", "snippet": "测试摘要"}
        ])
        yield mock


@pytest.fixture
def mock_orchestrator():
    """Mock总控Agent，避免调用LLM - patch到chat模块中的引用"""
    with patch('app.api.chat.orchestrator_agent') as mock:
        mock.process_message = AsyncMock(return_value={
            "type": "chat",
            "content": "这是模拟的AI响应内容",
            "stage": 1
        })
        # 模拟流式处理
        async def fake_stream(*args, **kwargs):
            yield {"type": "text", "content": "这是"}
            yield {"type": "text", "content": "模拟的"}
            yield {"type": "meta", "stage": 1, "sources": []}
        mock.process_message_stream = fake_stream
        yield mock


@pytest.fixture
def mock_ten_year_agent():
    """Mock十年战略分析Agent - patch到report模块中的引用"""
    with patch('app.api.report.ten_year_agent') as mock:
        mock.analyze = AsyncMock(return_value={
            "title": "十年战略分析报告",
            "content": "# 十年战略分析\n\n模拟报告内容",
            "sources": [{"title": "测试来源", "link": "https://example.com"}]
        })
        yield mock


@pytest.fixture
def mock_five_year_agent():
    """Mock五年关键驱动因素Agent - patch到report模块中的引用"""
    with patch('app.api.report.five_year_agent') as mock:
        mock.analyze = AsyncMock(return_value={
            "title": "五年关键驱动因素分析",
            "content": "# 五年分析\n\n模拟报告内容",
            "sources": []
        })
        yield mock


@pytest.fixture
def mock_three_year_agent():
    """Mock三年阶段性目标Agent - patch到report模块中的引用"""
    with patch('app.api.report.three_year_agent') as mock:
        mock.analyze = AsyncMock(return_value={
            "title": "三年阶段性目标",
            "content": "# 三年目标\n\n模拟报告内容",
            "sources": []
        })
        yield mock


@pytest.fixture
def mock_one_year_agent():
    """Mock一年任务分解Agent - patch到report模块中的引用"""
    with patch('app.api.report.one_year_agent') as mock:
        mock.analyze = AsyncMock(return_value={
            "title": "一年任务分解与战略屋",
            "content": "# 一年计划\n\n模拟报告内容",
            "sources": []
        })
        yield mock