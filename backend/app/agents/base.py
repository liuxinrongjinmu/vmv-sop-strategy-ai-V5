from typing import Dict, Any, List
import re
import time
import logging
from app.services.llm import llm_service
from app.services.search import search_service

logger = logging.getLogger(__name__)


class BaseAgent:
    """
    战略分析Agent基类
    提供通用的上下文构建、搜索、报告生成和降级逻辑
    """

    name: str = "base_agent"
    report_title: str = "战略分析报告"

    def __init__(self):
        pass

    async def analyze(self, prediction: str, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        执行战略分析（子类可覆盖）
        """
        raise NotImplementedError

    def _build_context(self, session_info: Dict, chat_history: List[Dict], uploaded_files: List[Dict]) -> str:
        """构建上下文信息文本"""
        parts = []

        company_name = session_info.get('company_name', '未提供')
        industry = session_info.get('industry', '未提供')
        stage = session_info.get('stage', '未提供')
        track = session_info.get('selected_track', '未提供')
        vision = session_info.get('vision', '')
        mission = session_info.get('mission', '')

        parts.append("## 企业信息")
        parts.append(f"- 企业名称：{company_name}")
        parts.append(f"- 行业领域：{industry}")
        parts.append(f"- 发展阶段：{stage}")
        parts.append(f"- 选定赛道：{track}")
        if vision:
            parts.append(f"- 愿景：{vision[:100]}")
        if mission:
            parts.append(f"- 使命：{mission[:100]}")

        if chat_history:
            parts.append("\n## 对话记录（最近）")
            for msg in chat_history[-5:]:
                role_label = "用户" if msg['role'] == 'user' else "顾问"
                content_preview = msg['content'][:150] + ("..." if len(msg['content']) > 150 else "")
                parts.append(f"- **{role_label}**：{content_preview}")

        if uploaded_files:
            parts.append("\n## 上传文件")
            for f in uploaded_files[:2]:
                filename = f.get('filename', '')
                content_preview = f.get('content', '')[:200]
                parts.append(f"- **{filename}**：{content_preview}...")

        return "\n".join(parts)

    async def _search_evidence(self, prediction: str, session_info: Dict, search_queries: List[str] = None) -> tuple:
        """
        搜索外部数据支撑论据
        子类可通过 search_queries 参数自定义搜索查询
        """
        track = session_info.get("selected_track", "")
        industry = session_info.get("industry", "")

        if search_queries is None:
            search_queries = []
            if track:
                search_queries.append(f"{track} 行业趋势 市场规模")
            if industry and industry != track:
                search_queries.append(f"{industry} 发展前景 竞争格局")

        keywords = re.findall(r'[\u4e00-\u9fa5]{2,6}(?:市场|行业|技术|趋势|增长|发展|竞争)', prediction)
        for kw in keywords[:2]:
            search_queries.append(kw)

        all_results = []
        for query in search_queries[:3]:
            try:
                results = await search_service.search(query, num_results=3)
                all_results.extend(results)
                logger.info(f"搜索 '{query}' 返回 {len(results)} 条结果")
            except Exception as e:
                logger.warning(f"搜索 '{query}' 失败: {e}")

        seen_urls = set()
        unique_results = []
        for r in all_results:
            url = r.get("link", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(r)

        search_context = ""
        if unique_results:
            parts = ["\n## 搜索到的外部数据（请在报告中引用这些数据来支撑论据）\n"]
            for i, r in enumerate(unique_results[:8], 1):
                title = r.get("title", "")
                snippet = r.get("snippet", "")
                link = r.get("link", "")
                parts.append(f"### 来源 {i}: {title}")
                parts.append(f"摘要: {snippet}")
                parts.append(f"链接: {link}\n")
            search_context = "\n".join(parts)

        sources = [
            {"title": r.get("title", ""), "url": r.get("link", ""), "snippet": r.get("snippet", "")}
            for r in unique_results[:8]
        ]

        return sources, search_context

    async def _generate_with_fallback(
        self,
        prediction: str,
        context_text: str,
        search_context: str,
        generate_full,
        generate_simplified,
        default_report_func
    ) -> Dict[str, Any]:
        """
        带降级的报告生成流程：完整版 → 简化版 → 默认版
        """
        start_time = time.time()

        try:
            content = await generate_full(prediction, context_text, search_context)
            elapsed = time.time() - start_time
            logger.info(f"{self.name}: 完整报告生成完成, 耗时{elapsed:.2f}秒")
            return {"title": self.report_title, "content": content, "sources": []}
        except Exception as e:
            logger.error(f"{self.name}: 完整版失败: {e}, 尝试简化版...")

        try:
            content = await generate_simplified(prediction, context_text, search_context)
            elapsed = time.time() - start_time
            logger.info(f"{self.name}: 简化版报告生成完成, 耗时{elapsed:.2f}秒")
            return {"title": self.report_title, "content": content, "sources": []}
        except Exception as e:
            logger.error(f"{self.name}: 简化版也失败: {e}, 返回默认报告")

        return {"title": self.report_title, "content": default_report_func(prediction), "sources": []}
