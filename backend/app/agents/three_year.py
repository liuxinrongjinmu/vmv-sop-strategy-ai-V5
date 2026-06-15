from typing import Dict, Any, List
import logging
from app.agents.base import BaseAgent
from app.services.llm import llm_service
from app.prompts.three_year import get_three_year_prompt

logger = logging.getLogger(__name__)


class ThreeYearAgent(BaseAgent):
    """
    三年战略Agent
    聚焦"阶段性目标"设定

    基于十年预判和五年关键驱动因素，确立三年阶段性目标。
    核心理念："当下的最优解相加大概率不等于长期最优解"，
    因此三年目标必须确保把握趋势，为十年后占一席之地奠定基础。
    """

    name = "three_year_strategy"
    report_title = "三年战略阶段性目标分析报告"

    async def analyze(
        self,
        prediction: str,
        context: Dict[str, Any],
        ten_year_report: str = "",
        five_year_report: str = "",
    ) -> Dict[str, Any]:
        """
        执行三年战略分析

        :param prediction: 用户的预判内容
        :param context: 包含session_info, chat_history, uploaded_files
        :param ten_year_report: 十年战略报告内容（如果有）
        :param five_year_report: 五年战略报告内容（如果有）
        :return: {"title": "...", "content": "...", "sources": [...]}
        """
        session_info = context.get("session_info", {})
        chat_history = context.get("chat_history", [])
        uploaded_files = context.get("uploaded_files", [])

        logger.info(f"三年战略分析开始... 预测: {prediction[:80]}...")

        # 构建上下文信息
        context_text = self._build_context(session_info, chat_history, uploaded_files)

        # 搜索外部数据支撑（自定义搜索查询——聚焦行业标杆和市场规模）
        search_queries = []
        track = session_info.get("selected_track", "")
        industry = session_info.get("industry", "")
        if track:
            search_queries.append(f"{track} 标杆企业 三年战略 目标规划")
        if industry and industry != track:
            search_queries.append(f"{industry} 龙头企业 发展战略 目标")
        search_queries.append(f"{track or industry} 市场规模预测 未来三年")
        search_results, search_context = await self._search_evidence(
            prediction, session_info, search_queries=search_queries
        )

        # 带降级的报告生成
        result = await self._generate_with_fallback(
            prediction, context_text, search_context,
            lambda p, c, s: self._generate_report_single_call(p, c, s, ten_year_report, five_year_report),
            lambda p, c, s: self._generate_simplified_report(p, c, s, ten_year_report, five_year_report),
            self._get_default_report
        )
        result["sources"] = search_results
        return result

    async def _generate_report_single_call(
        self,
        prediction: str,
        context_text: str,
        search_context: str = "",
        ten_year_report: str = "",
        five_year_report: str = "",
    ) -> str:
        """单次LLM调用生成完整三年战略报告（深度版）"""

        search_section = ""
        if search_context:
            search_section = f"""
{search_context}

**重要：** 请在目标设定和资源配置分析中，积极引用上述搜索到的外部数据来支撑你的论证。引用时标注"据外部数据"或"根据行业报告"。
"""

        ten_year_section = ""
        if ten_year_report:
            ten_year_section = f"""
## 十年战略预判报告（已生成）
{ten_year_report[:2000]}
"""

        five_year_section = ""
        if five_year_report:
            five_year_section = f"""
## 五年战略关键驱动因素报告（已生成）
{five_year_report[:2000]}
"""

        strategy_base_section = ""
        if ten_year_section or five_year_section:
            strategy_base_section = f"""
{ten_year_section}
{five_year_section}

**重要：** 三年目标必须基于上述十年预判方向和五年关键驱动因素来设定，确保战略逻辑链的连贯性。核心原则——"当下的最优解相加大概率不等于长期最优解"，三年目标要确保把握趋势，为十年后占一席之地奠定基础。
"""

        prompt = get_three_year_prompt(prediction, context_text, strategy_base_section, search_section)

        response = await llm_service.generate(
            prompt, temperature=0.35, max_tokens=6000
        )

        # 清理响应内容
        content = response.strip()

        # 确保以标题开头
        if not content.startswith("#"):
            content = "# 三年战略阶段性目标分析报告\n\n" + content

        return content

    async def _generate_simplified_report(
        self,
        prediction: str,
        context_text: str,
        search_context: str = "",
        ten_year_report: str = "",
        five_year_report: str = "",
    ) -> str:
        """备用方案：生成简化版三年战略报告"""

        search_hint = ""
        if search_context:
            search_hint = (
                "\n\n请参考以下外部数据支撑你的分析：\n" + search_context[:1500]
            )

        ten_year_hint = ""
        if ten_year_report:
            ten_year_hint = (
                "\n\n十年战略报告核心结论：\n" + ten_year_report[:800]
            )

        five_year_hint = ""
        if five_year_report:
            five_year_hint = (
                "\n\n五年战略关键驱动因素：\n" + five_year_report[:800]
            )

        prompt = f"""基于以下信息生成简化的三年战略阶段性目标分析报告（Markdown格式）：

{context_text}
{search_hint}
{ten_year_hint}
{five_year_hint}

用户预判：{prediction}

请包含：目标摘要、战略基础回顾、2-3个三年目标（含定性+定量）、目标逻辑验证、4-6个关键里程碑、资源配置需求概要、风险与调整机制、目标追踪指标。
每个部分精简到150字以内。直接输出报告内容。"""

        response = await llm_service.generate(
            prompt, temperature=0.5, max_tokens=2500
        )
        return response.strip()

    def _get_default_report(self, prediction: str) -> str:
        """返回默认报告（兜底方案）"""
        return f"""# 三年战略阶段性目标分析报告

## 一、目标摘要
基于十年预判方向和五年关键驱动因素，设定三年阶段性目标，聚焦市场地位、产品技术、组织能力三个维度，确保把握趋势为长期发展奠定基础。

---

## 二、战略基础回顾

### 2.1 十年预判核心结论
{prediction[:200]}

### 2.2 五年关键驱动因素
- 技术创新加速（近距/高借势）
- 政策环境变化（中距/中借势）
- 消费习惯演变（近距/高借势）

### 2.3 战略逻辑链
十年方向 → 五年驱动因素识别 → 三年目标设定 → 阶段性落地

---

## 三、三年目标设定

### 3.1 市场地位目标
**定性描述：** 在核心赛道建立显著市场地位，成为细分领域的重要参与者
**定量指标：**
- 核心指标1：市场份额达到5%以上
- 核心指标2：品牌认知度进入行业前10
**达成难度评估：** 中

### 3.2 产品技术目标
**定性描述：** 建立核心技术能力，产品达到行业领先水平
**定量指标：**
- 核心指标1：完成2-3个核心产品迭代
- 核心指标2：技术专利/知识产权5项以上
**达成难度评估：** 中

### 3.3 组织能力目标
**定性描述：** 建立与战略匹配的组织架构和人才体系
**定量指标：**
- 核心指标1：核心团队到位率90%以上
- 核心指标2：人效提升30%
**达成难度评估：** 低

---

## 四、目标逻辑验证

| 三年目标 | 对应五年驱动因素 | 支撑十年方向 | 逻辑完整性 |
|---------|----------------|------------|-----------|
| 市场地位 | 消费习惯演变 | 赛道占位 | 强 |
| 产品技术 | 技术创新加速 | 核心能力 | 强 |
| 组织能力 | 政策环境变化 | 可持续发展 | 中 |

逻辑链整体自洽，需关注组织能力目标与业务目标的匹配度。

---

## 五、关键里程碑

| 时间节点 | 里程碑事件 | 对应目标 | 交付物 |
|---------|-----------|---------|--------|
| 第1年Q1 | 核心团队组建 | 组织能力 | 团队到位 |
| 第1年Q2 | 首款产品上线 | 产品技术 | 产品发布 |
| 第1年Q4 | 首批客户获取 | 市场地位 | 客户案例 |
| 第2年Q2 | 产品迭代V2 | 产品技术 | 产品升级 |
| 第2年Q4 | 市场拓展加速 | 市场地位 | 市场报告 |
| 第3年Q4 | 目标全面达成 | 全部 | 评估报告 |

---

## 六、资源配置需求

### 6.1 人才需求
- 核心岗位：技术负责人、产品负责人、市场负责人
- 招聘时间表：第1年Q1-Q2完成核心岗位招聘

### 6.2 资金需求
- 三年总资金需求：根据企业规模估算
- 资金用途：研发40%、市场30%、人才20%、储备10%

---

## 七、风险与调整机制

**风险1: 市场拓展不及预期** - 概率：中 | 影响：高 | 应对：调整市场策略
**风险2: 核心人才流失** - 概率：低 | 影响：高 | 应对：建立激励机制
**风险3: 技术路线偏差** - 概率：中 | 影响：中 | 应对：保持技术灵活性

**调整触发条件：** 关键里程碑连续2个季度未达成时启动目标调整

---

## 八、目标追踪指标

| 目标 | 核心追踪指标 | 检查频率 | 预警阈值 |
|------|------------|---------|---------|
| 市场地位 | 市场份额 | 月度 | 低于目标50% |
| 产品技术 | 产品迭代进度 | 周度 | 延迟超过2周 |
| 组织能力 | 团队到位率 | 月度 | 低于80% |"""


three_year_agent = ThreeYearAgent()
