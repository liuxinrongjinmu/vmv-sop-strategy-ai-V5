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
        """单次LLM调用生成完整报告（深度版）"""
        
        prompt = f"""你是一位拥有15年经验的资深战略咨询顾问，擅长行业分析和战略规划。请基于以下信息，生成一份**深入、专业、有据可依**的十年战略预判分析报告。

{context_text}

## 用户预判
{prediction}

---

请直接输出完整的Markdown格式报告，**总字数不少于3500字**，包含以下结构：

# 十年战略预判分析报告

## 一、预判摘要
（120-180字，完整概括用户的核心预判、关键趋势判断、主要机会点）

---

## 二、正面论据分析
（至少2-3个论据，每个都要深入分析）

### 2.X 论据标题（如"高净值人群对延年益寿需求增长"）
**核心观点：** （20-30字）

**论证过程：**
（**300-450字深度论证**，必须：
- 引用具体的市场数据、行业趋势或用户提供的背景信息
- 分析需求产生的根本原因和驱动力
- 说明为什么这对企业是机会
- **禁止臆测企业未提供的信息**，如不确定则标注"基于有限信息"
- 使用专业术语但保持可读性）

**数据支持：**
- 具体数据点1（如"中国高净值人群规模预计2025年达到XXX万"）
- 具体数据点2
- 具体数据点3

**逻辑推演步骤：**
1. （具体步骤1，20字内）
2. （具体步骤2，20字内）
3. （具体步骤3，20字内）
4. （具体步骤4，20字内）

**对企业启示：** （80-120字，给出具体的战略建议方向）

---

## 三、反面论据分析
（至少2-3个风险点，每个都要深入分析）

### 3.X 风险标题（如"市场认知度低"或"初期资源有限"）
**核心风险：** （20-30字）

**风险深度分析：**
（**300-450字深度分析**，必须：
- 详细描述风险的具体表现和影响机制
- 分析风险发生的可能性和时间节点
- 说明该风险对企业可能造成的具体损失
- 区分"已知风险"和"假设性风险"，后者要明确标注
- 不要为了凑数而编造风险，只分析真实存在的挑战）

**风险指标：**
- 具体指标1（如"获客成本高于行业平均XX%"）
- 具体指标2
- 具体指标3

**对企业影响：** （80-120字，说明具体影响哪些业务环节）
**应对措施：** （80-120字，给出可操作的应对方案）

---

## 四、综合判断

### 4.1 可信度评估
**等级：** 高/中/低 | **评分：** XX/100
**理由：** （80-120字评分理由，说明打分依据和不确定性来源）

### 4.2 SWOT分析
- **优势：** （2-3个，每项20字内）
- **劣势：** （2-3个，每项20字内）
- **机会：** （2-3个，每项20字内）
- **威胁：** （2-3个，每项20字内）

### 4.3 关键变量识别
（至少3-5个变量）
**变量名** - 详细说明（40字内）（影响：正向/负向 | 重要程度：高/中/低 | 监测方法：30字内）

### 4.4 情景分析
- **乐观情景：** （50-80字，描述最佳情况及发生条件）
- **基准情景：** （50-80字，描述最可能情况）
- **悲观情景：** （50-80字，描述最差情况及触发条件）
- （每种情景注明大致概率）

### 4.5 行动建议
（至少3条，按优先级排序）
**建议X: 具体行动名称** - 理由：（60-100字）| 优先级：高/中/低 | 时间框架：具体时间 | 预期效果：（30字内）

### 4.6 风险应对策略
（针对上述反面论据中的主要风险）
**风险X: 风险名称** - 应对策略：（60-100字具体方案）| 触发条件预案：（40字内）

### 4.7 综合判断总结
（200-300字深度总结，必须包含：
- 整体评价（该预判的合理性和可行性）
- 核心成功因素（3-4个关键成功要素）
- 主要风险提示（2-3个必须警惕的风险点）
- 战略方向建议（未来3-5年的发展路径）
- 最终结论（对该企业/赛道的总体判断）

---

**核心原则（违反将导致报告质量下降）：**
1. **事实优先**：所有结论必须有依据，禁止凭空臆测企业业务模式
2. **透明标注**：信息不足时必须明确写明"基于有限信息的分析"
3. **深度分析**：每个论据和风险都要有实质性的分析内容，不要泛泛而谈
4. **数据支撑**：尽量引用具体数字、比例、趋势等量化信息
5. ** actionable**：所有建议都应该是可执行的，而非空泛的方向性描述
6. 直接输出Markdown报告正文，不要有任何前缀解释"""

        response = await llm_service.generate(prompt, temperature=0.35, max_tokens=6000)
        
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