from typing import Dict, Any, List
import time
import logging
from app.agents.base import BaseAgent
from app.services.llm import llm_service
from app.prompts.five_year import get_five_year_prompt

logger = logging.getLogger(__name__)


class FiveYearAgent(BaseAgent):
    """
    五年关键驱动因素Agent
    基于十年战略预判，分析五年关键驱动因素
    """

    name = "five_year_strategy"
    report_title = "五年关键驱动因素分析报告"

    async def analyze(
        self,
        prediction: str,
        context: Dict[str, Any],
        ten_year_report: str = ""
    ) -> Dict[str, Any]:
        """
        执行五年关键驱动因素分析
        :param prediction: 用户预判内容
        :param context: 会话上下文（session_info, chat_history, uploaded_files）
        :param ten_year_report: 前序十年战略报告内容
        :return: {title, content, sources}
        """
        session_info = context.get("session_info", {})
        chat_history = context.get("chat_history", [])
        uploaded_files = context.get("uploaded_files", [])

        logger.info(f"开始五年分析... 预测: {prediction[:80]}...")

        # 构建上下文信息
        context_text = self._build_context(session_info, chat_history, uploaded_files)

        # 搜索外部数据支撑（自定义搜索查询）
        search_queries = []
        track = session_info.get("selected_track", "")
        industry = session_info.get("industry", "")
        if track:
            search_queries.append(f"{track} 驱动因素 关键成功要素")
        if industry and industry != track:
            search_queries.append(f"{industry} 五年趋势 核心变量")
        search_results, search_context = await self._search_evidence(
            prediction, session_info, search_queries=search_queries
        )

        # 构建前序报告上下文
        prev_report_section = ""
        if ten_year_report:
            prev_report_section = f"""
## 十年战略预判报告（前序报告）
{ten_year_report}

**重要：** 请基于上述十年战略预判报告的结论，进行五年关键驱动因素分析。确保五年分析与十年预判保持逻辑一致性。
"""

        # 带降级的报告生成
        result = await self._generate_with_fallback(
            prediction, context_text, search_context,
            lambda p, c, s: self._generate_report_single_call(p, c, s, prev_report_section),
            lambda p, c, s: self._generate_simplified_report(p, c, s, prev_report_section),
            self._get_default_report
        )
        result["sources"] = search_results
        return result

    async def _generate_report_single_call(
        self, prediction: str, context_text: str, search_context: str = "", prev_report_section: str = ""
    ) -> str:
        """单次LLM调用生成五年关键驱动因素分析报告"""

        search_section = ""
        if search_context:
            search_section = f"""
{search_context}

**重要：** 请在驱动因素分析中，积极引用上述搜索到的外部数据来支撑你的论证。引用时标注"据外部数据"或"根据行业报告"。
"""

        prompt = get_five_year_prompt(prediction, context_text, prev_report_section, search_section)

        response = await llm_service.generate(prompt, temperature=0.35, max_tokens=6000)

        content = response.strip()
        if not content.startswith("#"):
            content = "# 五年关键驱动因素分析报告\n\n" + content

        return content

    async def _generate_simplified_report(
        self, prediction: str, context_text: str, search_context: str = "", prev_report_section: str = ""
    ) -> str:
        """备用方案：生成简化版五年分析报告"""

        search_hint = ""
        if search_context:
            search_hint = "\n\n请参考以下外部数据支撑你的分析：\n" + search_context[:1500]

        prompt = f"""基于以下信息生成简化的五年关键驱动因素分析报告（Markdown格式）：

{context_text}
{prev_report_section}
{search_hint}

用户预判：{prediction}

请包含：分析摘要、3个关键驱动因素（每个含描述、影响机制、趋势预判）、发展路径推演、战略聚焦建议、风险与不确定性。
每个部分精简到100字以内。直接输出报告内容。"""

        response = await llm_service.generate(prompt, temperature=0.5, max_tokens=2000)
        return response.strip()

    def _get_default_report(self, prediction: str) -> str:
        """返回默认五年分析报告（兜底方案）"""
        return f"""# 五年关键驱动因素分析报告

## 一、分析摘要
基于十年战略预判，识别出影响行业未来五年发展的关键驱动因素，为企业战略聚焦提供依据。

---

## 二、关键驱动因素识别

### 2.1 市场需求驱动
**因素描述：** 市场需求持续演变推动行业变革
**影响机制：** 消费升级和技术进步共同推动市场需求变化，企业需紧跟趋势调整战略。
**五年趋势预判：** 需求将向高端化、个性化方向发展。
**对企业启示：** 提前布局产品线，满足新兴需求。

### 2.2 技术创新驱动
**因素描述：** 核心技术突破加速行业迭代
**影响机制：** 技术创新降低成本、提升效率，改变竞争格局。
**五年趋势预判：** 关键技术将逐步成熟并规模化应用。
**对企业启示：** 加大技术投入，建立技术壁垒。

### 2.3 政策环境驱动
**因素描述：** 政策导向影响行业发展方向
**影响机制：** 政策支持或监管变化直接影响市场准入和竞争规则。
**五年趋势预判：** 行业监管将趋于规范，合规要求提高。
**对企业启示：** 密切关注政策动向，提前做好合规准备。

---

## 三、驱动因素关联分析

### 3.1 因素间相互作用
- 市场需求与技术革新相互促进
- 政策环境为技术创新提供方向指引

### 3.2 核心因果链
市场需求升级 → 技术创新加速 → 竞争格局重塑

---

## 四、五年发展路径推演

### 4.1 基准路径
行业稳步发展，关键技术逐步成熟，市场格局趋于稳定。

### 4.2 加速路径
技术突破超预期，市场快速扩容，先发者获得显著优势。

### 4.3 阻滞路径
技术进展不及预期，政策收紧，市场竞争加剧。

---

## 五、战略聚焦建议

### 5.1 核心聚焦领域
1. 核心技术能力建设
2. 差异化市场定位
3. 合规与风控体系

### 5.2 资源配置建议
优先投入技术研发和市场拓展，适度配置合规资源。

### 5.3 关键里程碑
- 第1-2年：技术验证与市场测试
- 第3-4年：规模化扩张
- 第5年：行业地位巩固

---

## 六、风险与不确定性

### 6.1 关键假设
- 市场需求持续增长
- 技术发展符合预期
- 政策环境相对稳定

### 6.2 预警信号
- 核心技术进展滞后
- 主要竞争对手异动
- 政策方向重大调整"""


five_year_agent = FiveYearAgent()
