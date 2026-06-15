from typing import Dict, Any, List
import time
import logging
from app.agents.base import BaseAgent
from app.services.llm import llm_service
from app.prompts.ten_year import get_ten_year_prompt

logger = logging.getLogger(__name__)

class TenYearAgent(BaseAgent):
    """
    十年战略Agent
    负责赛道预判分析，生成正反论据和综合判断
    
    极速版：单次LLM调用生成完整报告，避免多步超时累积
    """
    
    name = "ten_year_strategy"
    report_title = "十年战略预判分析报告"
    
    async def analyze(self, prediction: str, context: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        执行十年战略分析
        流程：搜索外部数据 → 单次LLM调用生成报告
        """
        session_info = context.get("session_info", {})
        chat_history = context.get("chat_history", [])
        uploaded_files = context.get("uploaded_files", [])
        
        logger.info(f"开始分析... 预测: {prediction[:80]}...")
        
        # 构建上下文信息
        context_text = self._build_context(session_info, chat_history, uploaded_files)
        
        # 搜索外部数据支撑
        search_results, search_context = await self._search_evidence(prediction, session_info)
        
        # 带降级的报告生成
        result = await self._generate_with_fallback(
            prediction, context_text, search_context,
            self._generate_report_single_call,
            self._generate_simplified_report,
            self._get_default_report
        )
        result["sources"] = search_results
        return result
    
    async def _generate_report_single_call(
        self, prediction: str, context_text: str, search_context: str = ""
    ) -> str:
        """单次LLM调用生成完整报告（深度版）"""

        search_section = ""
        if search_context:
            search_section = f"""
{search_context}

**重要：** 请在正面论据和反面论据的分析中，积极引用上述搜索到的外部数据来支撑你的论证。引用时标注"据外部数据"或"根据行业报告"。
"""

        prompt = get_ten_year_prompt(prediction, context_text, search_section)

        response = await llm_service.generate(prompt, temperature=0.35, max_tokens=6000)

        # 清理响应内容
        content = response.strip()

        # 确保以标题开头
        if not content.startswith("#"):
            content = "# 十年战略预判分析报告\n\n" + content

        return content
    
    async def _generate_simplified_report(
        self, prediction: str, context_text: str, search_context: str = ""
    ) -> str:
        """备用方案：生成简化版报告"""
        
        search_hint = ""
        if search_context:
            search_hint = "\n\n请参考以下外部数据支撑你的分析：\n" + search_context[:1500]
        
        prompt = f"""基于以下信息生成简化的十年战略预判分析报告（Markdown格式）：

{context_text}
{search_hint}

用户预判：{prediction}

请包含：预判摘要、2个正面论据、2个反面论据、SWOT分析、3条行动建议、总结。
每个部分精简到100字以内。直接输出报告内容。"""

        response = await llm_service.generate(prompt, temperature=0.5, max_tokens=2000)
        return response.strip()
    
    def _get_default_report(self, prediction: str) -> str:
        """返回默认报告（兜底方案）"""
        return f"""# 十年战略预判分析报告

## 一、预判摘要
{prediction[:200]}

---

## 二、正面论据分析

### 2.1 市场机遇
**核心观点：** 市场需求持续增长

**论证过程：**
根据用户预判，该赛道存在明显的市场机遇。随着技术进步和消费升级，相关市场规模预计将持续扩大。

**逻辑推演步骤：**
1. 市场需求识别
2. 技术可行性验证
3. 商业模式构建

**对企业启示：** 把握时机，快速进入市场

### 2.2 竞争优势
**核心观点：** 差异化定位带来优势

**论证过程：**
通过差异化产品和服务，可以在竞争中建立独特优势。

**对企业启示：** 强化核心竞争力

---

## 三、反面论据分析

### 3.1 市场风险
**核心风险：** 市场不确定性

**风险深度分析：**
市场环境变化快，竞争激烈，存在一定的不确定性。

**应对措施：** 保持灵活，持续监控市场变化

### 3.2 资源约束
**核心风险：** 资源有限制约发展

**应对措施：** 合理配置资源，分阶段投入

---

## 四、综合判断

### 4.1 可信度评估
**等级：** 中 | **评分：** 65/100
**理由：** 预判具有一定合理性，但需更多数据支持

### 4.2 SWOT分析
- **优势：** 市场机遇明显
- **劣势：** 信息有限
- **机会：** 行业增长趋势
- **威胁：** 竞争加剧

### 4.3 关键变量识别
**市场需求** - 核心驱动力（影响：正向/高）

### 4.4 情景分析
- **乐观：** 快速占领市场份额
- **基准：** 稳步发展
- **悲观：** 面临激烈竞争

### 4.5 行动建议
**建议1:** 深入市场调研 | 优先级：高 | 时间：立即
**建议2:** 明确差异化定位 | 优先级：高 | 时间：1个月内
**建议3:** 制定阶段性目标 | 优先级：中 | 时间：3个月内

### 4.6 综合判断总结
预判具有参考价值，建议结合实际情况制定灵活战略。关键成功因素包括市场洞察力、执行力和资源整合能力。主要风险来自市场竞争和外部环境变化。"""

ten_year_agent = TenYearAgent()
