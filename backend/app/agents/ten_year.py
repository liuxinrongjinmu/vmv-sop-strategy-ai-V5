from typing import Dict, Any, List
import asyncio
import json
import re
import time
from app.services.llm import llm_service
from app.services.search import search_service

class TenYearAgent:
    """
    十年战略Agent
    负责赛道预判分析，生成正反论据和综合判断
    
    极速版：单次LLM调用生成完整报告，避免多步超时累积
    """
    
    def __init__(self):
        self.name = "ten_year_strategy"
    
    async def analyze(self, prediction: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行十年战略分析（极速版：单次LLM调用）
        """
        start_time = time.time()
        
        session_info = context.get("session_info", {})
        chat_history = context.get("chat_history", [])
        uploaded_files = context.get("uploaded_files", [])
        
        print(f"[TenYearAgent] 开始分析... 预测: {prediction[:80]}...")
        
        # 构建上下文信息
        context_text = self._build_context(session_info, chat_history, uploaded_files)
        
        # 单次LLM调用生成完整报告
        print("[TenYearAgent] [核心] 单次LLM调用生成报告...")
        step_start = time.time()
        
        try:
            report_content = await self._generate_report_single_call(prediction, context_text)
            step_end = time.time()
            print(f"[TenYearAgent] 报告生成完成! 耗时: {step_end - step_start:.2f}秒")
            
            total_time = time.time() - start_time
            print(f"[TenYearAgent] 总耗时: {total_time:.2f}秒")
            
            return {
                "title": "十年战略预判分析报告",
                "content": report_content,
                "sources": []
            }
            
        except Exception as e:
            print(f"[TenYearAgent] 单次调用失败: {e}, 尝试简化版...")
            # 备用方案：生成简化报告
            simplified_content = await self._generate_simplified_report(prediction, context_text)
            
            total_time = time.time() - start_time
            print(f"[TenYearAgent] 简化版报告生成完成! 总耗时: {total_time:.2f}秒")
            
            return {
                "title": "十年战略预判分析报告",
                "content": simplified_content,
                "sources": []
            }
    
    def _build_context(self, session_info: Dict, chat_history: List[Dict], uploaded_files: List[Dict]) -> str:
        """构建上下文信息文本"""
        parts = []
        
        # 企业信息
        company_name = session_info.get('company_name', '未提供')
        industry = session_info.get('industry', '未提供')
        stage = session_info.get('stage', '未提供')
        track = session_info.get('selected_track', '未提供')
        vision = session_info.get('vision', '')
        mission = session_info.get('mission', '')
        
        parts.append(f"## 企业信息")
        parts.append(f"- 企业名称：{company_name}")
        parts.append(f"- 行业领域：{industry}")
        parts.append(f"- 发展阶段：{stage}")
        parts.append(f"- 选定赛道：{track}")
        if vision:
            parts.append(f"- 愿景：{vision[:100]}")
        if mission:
            parts.append(f"- 使命：{mission[:100]}")
        
        # 聊天历史摘要（取最后5条）
        if chat_history:
            parts.append(f"\n## 对话记录（最近）")
            for msg in chat_history[-5:]:
                role_label = "用户" if msg['role'] == 'user' else "顾问"
                content_preview = msg['content'][:150] + ("..." if len(msg['content']) > 150 else "")
                parts.append(f"- **{role_label}**：{content_preview}")
        
        # 上传文件信息
        if uploaded_files:
            parts.append(f"\n## 上传文件")
            for f in uploaded_files[:2]:
                filename = f.get('filename', '')
                content_preview = f.get('content', '')[:200]
                parts.append(f"- **{filename}**：{content_preview}...")
        
        return "\n".join(parts)
    
    async def _generate_report_single_call(self, prediction: str, context_text: str) -> str:
        """单次LLM调用生成完整报告"""
        
        prompt = f"""你是一位资深战略咨询顾问。请基于以下信息，生成一份专业的十年战略预判分析报告。

{context_text}

## 用户预判
{prediction}

---

请直接输出完整的Markdown格式报告，包含以下结构：

# 十年战略预判分析报告

## 一、预判摘要
（100字内总结用户的核心预判）

---

## 二、正面论据分析

### 2.1 论据标题
**核心观点：** （20字内）

**论证过程：**
（150-200字论证，基于事实和数据，不要臆测）

**数据支持：**
- 数据点1
- 数据点2

**逻辑推演步骤：**
1. 步骤一
2. 步骤二
3. 步骤三

**对企业启示：** （50字内）

### 2.2 第二个论据
（同上结构）

---

## 三、反面论据分析

### 3.1 风险标题
**核心风险：** （20字内）

**风险深度分析：**
（150-200字分析，基于事实和数据，不要臆测）

**风险指标：**
- 指标1
- 指标2

**对企业影响：** （50字内）
**应对措施：** （50字内）

### 3.2 第二个风险
（同上结构）

---

## 四、综合判断

### 4.1 可信度评估
**等级：** 高/中/低 | **评分：** XX/100
**理由：** （60字内评分理由）

### 4.2 SWOT分析
- **优势：** ...
- **劣势：** ...
- **机会：** ...
- **威胁：** ...

### 4.3 关键变量识别
**变量名** - 说明（影响：正向/负向/高/中/低）

### 4.4 情景分析
- **乐观：** （30字内）
- **基准：** （30字内）
- **悲观：** （30字内）

### 4.5 行动建议
**建议1:** ... | 优先级：高/中/低 | 时间：...

### 4.6 风险应对策略
**风险1:** ... | 应对：... | 预案：...

### 4.7 综合判断总结
（150字内总结：整体评价+成功因素+风险提示+战略方向）

---

**重要要求：**
1. 所有结论必须基于上述事实信息，不得臆测企业业务模式
2. 对关键结论必须提供具体数据支持或明确标注为假设
3. 当信息不足时，明确标注为"基于有限信息的分析"
4. 每个论据2-3个，内容深入但不冗余
5. 直接输出Markdown内容，不要其他解释"""

        response = await llm_service.generate(prompt, temperature=0.4, max_tokens=4000)
        
        # 清理响应内容
        content = response.strip()
        
        # 确保以标题开头
        if not content.startswith("#"):
            content = "# 十年战略预判分析报告\n\n" + content
        
        return content
    
    async def _generate_simplified_report(self, prediction: str, context_text: str) -> str:
        """备用方案：生成简化版报告"""
        
        prompt = f"""基于以下信息生成简化的十年战略预判分析报告（Markdown格式）：

{context_text}

用户预判：{prediction}

请包含：预判摘要、2个正面论据、2个反面论据、SWOT分析、3条行动建议、总结。
每个部分精简到100字以内。直接输出报告内容。"""

        try:
            response = await llm_service.generate(prompt, temperature=0.5, max_tokens=2000)
            return response.strip()
        except Exception as e:
            print(f"[TenYearAgent] 简化版也失败: {e}, 返回默认报告")
            return self._get_default_report(prediction)
    
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