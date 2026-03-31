from typing import Dict, Any, List
from app.services.llm import llm_service
from app.services.search import search_service
import json

class TenYearAgent:
    """
    十年战略Agent
    负责赛道预判分析，生成正反论据和综合判断
    """
    
    def __init__(self):
        self.name = "ten_year_strategy"
    
    async def analyze(self, prediction: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行十年战略分析
        """
        session_info = context.get("session_info", {})
        chat_history = context.get("chat_history", [])
        uploaded_files = context.get("uploaded_files", [])
        
        key_insights = await self._extract_key_insights(chat_history, uploaded_files, session_info)
        
        enterprise_analysis = await self._analyze_enterprise(session_info, key_insights)
        
        assumptions = await self._extract_assumptions(prediction, key_insights, enterprise_analysis)
        
        search_results = await self._search_evidence(assumptions, session_info, key_insights, prediction)
        
        arguments = await self._build_arguments(
            prediction, assumptions, search_results, session_info, key_insights, enterprise_analysis
        )
        
        judgment = await self._generate_judgment(arguments, session_info, key_insights, enterprise_analysis)
        
        report = self._format_report(prediction, arguments, judgment, search_results, key_insights, enterprise_analysis)
        
        return report
    
    async def _extract_key_insights(
        self, 
        chat_history: List[Dict], 
        uploaded_files: List[Dict],
        session_info: Dict
    ) -> Dict[str, Any]:
        """
        从聊天历史和上传文件中提取关键洞察
        """
        insights = {
            "chat_summary": "",
            "file_insights": [],
            "key_decisions": [],
            "concerns": [],
            "opportunities": [],
            "mentioned_resources": [],
            "mentioned_advantages": [],
            "mentioned_challenges": []
        }
        
        if chat_history:
            chat_text = "\n".join([
                f"[{msg['role']}]: {msg['content']}" 
                for msg in chat_history[-20:]
            ])
            
            prompt = f"""请从以下对话历史中提取关键信息。

对话历史：
{chat_text}

请提取以下内容（严格按照JSON格式）：
{{
    "summary": "对话核心内容总结（100字以内）",
    "key_decisions": ["关键决策或判断1", "关键决策或判断2"],
    "concerns": ["用户关注的问题或担忧1", "用户关注的问题或担忧2"],
    "opportunities": ["识别到的机会1", "识别到的机会2"],
    "mentioned_resources": ["对话中提及的企业资源1", "对话中提及的企业资源2"],
    "mentioned_advantages": ["对话中提及的企业优势1", "对话中提及的企业优势2"],
    "mentioned_challenges": ["对话中提及的企业挑战1", "对话中提及的企业挑战2"]
}}"""
            
            try:
                response = await llm_service.generate(prompt, temperature=0.3, max_tokens=1000)
                json_start = response.find("{")
                json_end = response.rfind("}") + 1
                chat_insights = json.loads(response[json_start:json_end])
                insights["chat_summary"] = chat_insights.get("summary", "")
                insights["key_decisions"] = chat_insights.get("key_decisions", [])
                insights["concerns"] = chat_insights.get("concerns", [])
                insights["opportunities"] = chat_insights.get("opportunities", [])
                insights["mentioned_resources"] = chat_insights.get("mentioned_resources", [])
                insights["mentioned_advantages"] = chat_insights.get("mentioned_advantages", [])
                insights["mentioned_challenges"] = chat_insights.get("mentioned_challenges", [])
            except Exception as e:
                print(f"提取聊天洞察失败: {e}")
        
        for file_info in uploaded_files:
            filename = file_info.get("filename", "")
            content = file_info.get("content", "")
            
            if content:
                prompt = f"""请从以下文件内容中提取关键信息。

文件名：{filename}
文件内容摘要：
{content[:1500]}

请提取以下内容（严格按照JSON格式）：
{{
    "filename": "{filename}",
    "main_topic": "文件主要主题",
    "key_data": ["关键数据或事实1", "关键数据或事实2"],
    "resources_mentioned": ["文件中提及的资源信息1", "文件中提及的资源信息2"]
}}"""
                
                try:
                    response = await llm_service.generate(prompt, temperature=0.3, max_tokens=600)
                    json_start = response.find("{")
                    json_end = response.rfind("}") + 1
                    file_insight = json.loads(response[json_start:json_end])
                    insights["file_insights"].append(file_insight)
                except Exception as e:
                    print(f"提取文件洞察失败: {e}")
        
        return insights
    
    async def _analyze_enterprise(self, session_info: Dict, key_insights: Dict) -> Dict[str, Any]:
        """
        分析企业背景（精简版）
        """
        chat_summary = key_insights.get("chat_summary", "")
        mentioned_resources = key_insights.get("mentioned_resources", [])
        mentioned_advantages = key_insights.get("mentioned_advantages", [])
        mentioned_challenges = key_insights.get("mentioned_challenges", [])
        
        prompt = f"""基于以下信息，对企业进行简要背景分析。

## 企业基础信息
- 企业名称：{session_info.get('company_name', '未提供')}
- 所属行业：{session_info.get('industry', '未提供')}
- 企业阶段：{session_info.get('stage', '未提供')}
- 团队规模：{session_info.get('team_size', '未提供')}
- 选定赛道：{session_info.get('selected_track', '未提供')}
- 愿景：{session_info.get('vision', '未提供')}
- 使命：{session_info.get('mission', '未提供')}
- 价值观：{session_info.get('values', '未提供')}
- 补充信息：{session_info.get('additional_info', '未提供')}

## 对话中提及的信息
- 对话摘要：{chat_summary}
- 提及的资源：{', '.join(mentioned_resources) if mentioned_resources else '无'}
- 提及的优势：{', '.join(mentioned_advantages) if mentioned_advantages else '无'}
- 提及的挑战：{', '.join(mentioned_challenges) if mentioned_challenges else '无'}

请输出以下内容（严格按照JSON格式）：

{{
    "enterprise_profile": {{
        "name": "企业名称",
        "industry": "所属行业",
        "stage": "发展阶段",
        "track": "选定赛道"
    }},
    "resource_summary": "资源概况总结（80字以内）",
    "core_advantages": ["核心优势1", "核心优势2"],
    "core_disadvantages": ["核心劣势1", "核心劣势2"],
    "strategic_position": "当前战略定位（50字以内）"
}}"""

        try:
            response = await llm_service.generate(prompt, temperature=0.3, max_tokens=800)
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            enterprise_analysis = json.loads(response[json_start:json_end])
            return enterprise_analysis
        except Exception as e:
            print(f"企业分析失败: {e}")
            return {
                "enterprise_profile": {
                    "name": session_info.get("company_name", "未提供"),
                    "industry": session_info.get("industry", "未提供"),
                    "stage": session_info.get("stage", "未提供"),
                    "track": session_info.get("selected_track", "未提供")
                },
                "resource_summary": "企业资源处于发展积累阶段",
                "core_advantages": ["发展潜力"],
                "core_disadvantages": ["资源有限"],
                "strategic_position": "处于市场进入或成长阶段"
            }
    
    async def _extract_assumptions(self, prediction: str, key_insights: Dict, enterprise_analysis: Dict) -> List[str]:
        """
        从预判中提取关键假设
        """
        enterprise_profile = enterprise_analysis.get("enterprise_profile", {})
        
        prompt = f"""请从以下战略预判中提取4-6个关键假设。

战略预判：
{prediction}

企业背景：
- 企业：{enterprise_profile.get('name', '')}（{enterprise_profile.get('stage', '')}阶段）
- 赛道：{enterprise_profile.get('track', '')}

请提取支撑预判成立的关键假设，每个假设单独一行，不要编号。假设应该具体、可验证。

关键假设："""
        
        response = await llm_service.generate(prompt, temperature=0.3)
        assumptions = [line.strip() for line in response.split("\n") if line.strip()]
        return assumptions[:6]
    
    async def _search_evidence(
        self, 
        assumptions: List[str], 
        session_info: Dict,
        key_insights: Dict,
        prediction: str = ""
    ) -> Dict[str, List]:
        """
        搜索支持/反对假设的证据
        关键改进：使用预判内容构建更精准的搜索关键词
        """
        results = {
            "supporting": [],
            "opposing": []
        }
        
        track = session_info.get("selected_track", "")
        industry = session_info.get("industry", "")
        
        prediction_keywords = prediction[:100] if prediction else ""
        
        try:
            support_query = f"{track} {industry} {prediction_keywords} 市场分析 发展趋势 2024 2025"
            print(f"[Search] 支持性搜索: {support_query[:80]}...")
            support_results = await search_service.search(support_query, 5)
            for r in support_results:
                if r.get("link") and r.get("link").startswith("http"):
                    results["supporting"].append(r)
            
            oppose_query = f"{track} {industry} 风险 挑战 市场竞争 2024 2025"
            print(f"[Search] 反对性搜索: {oppose_query[:80]}...")
            oppose_results = await search_service.search(oppose_query, 5)
            for r in oppose_results:
                if r.get("link") and r.get("link").startswith("http"):
                    results["opposing"].append(r)
            
            for i, assumption in enumerate(assumptions[:2]):
                assumption_query = f"{track} {assumption[:50]}"
                print(f"[Search] 假设验证搜索{i+1}: {assumption_query[:80]}...")
                assumption_results = await search_service.search(assumption_query, 2)
                for r in assumption_results:
                    if r.get("link") and r.get("link").startswith("http"):
                        results["supporting"].append(r)
                        
        except Exception as e:
            print(f"搜索服务调用失败: {e}")
        
        seen_urls = set()
        unique_supporting = []
        unique_opposing = []
        
        for r in results["supporting"]:
            if r["link"] not in seen_urls:
                unique_supporting.append(r)
                seen_urls.add(r["link"])
        
        for r in results["opposing"]:
            if r["link"] not in seen_urls:
                unique_opposing.append(r)
                seen_urls.add(r["link"])
        
        results["supporting"] = unique_supporting[:8]
        results["opposing"] = unique_opposing[:8]
        
        print(f"[Search] 最终结果: 支持{len(results['supporting'])}条, 反对{len(results['opposing'])}条")
        
        return results
    
    async def _build_arguments(
        self,
        prediction: str,
        assumptions: List[str],
        search_results: Dict,
        session_info: Dict,
        key_insights: Dict,
        enterprise_analysis: Dict
    ) -> Dict[str, List]:
        """
        构建正反论据（重点部分，需要详细）
        """
        supporting_text = self._format_search_results_with_links(search_results["supporting"][:6])
        opposing_text = self._format_search_results_with_links(search_results["opposing"][:6])
        
        enterprise_profile = enterprise_analysis.get("enterprise_profile", {})
        resource_summary = enterprise_analysis.get("resource_summary", "")
        core_advantages = enterprise_analysis.get("core_advantages", [])
        core_disadvantages = enterprise_analysis.get("core_disadvantages", [])
        
        prompt = f"""你是一位资深的战略咨询顾问，拥有麦肯锡、BCG级别的专业分析能力。请基于以下信息，构建深度的战略分析论据。

## 企业背景
- 企业：{enterprise_profile.get('name', '')}（{enterprise_profile.get('stage', '')}阶段）
- 行业：{enterprise_profile.get('industry', '')}
- 赛道：{enterprise_profile.get('track', '')}
- 资源概况：{resource_summary}
- 核心优势：{', '.join(core_advantages) if core_advantages else '待建立'}
- 核心劣势：{', '.join(core_disadvantages) if core_disadvantages else '待改善'}

## 战略预判
{prediction}

## 关键假设
{chr(10).join(f'- {a}' for a in assumptions)}

## 外部参考信息（支持性）
{supporting_text if supporting_text else "无外部参考信息，请基于行业常识分析"}

## 外部参考信息（反对性）
{opposing_text if opposing_text else "无外部参考信息，请基于行业常识分析"}

---

**这是报告的核心部分，请深入分析，每个论据都要详细展开！**

请输出以下内容（严格按照JSON格式）：

{{
  "positive_arguments": [
    {{
      "title": "论据标题（简洁有力）",
      "core_point": "核心观点（一句话，20字以内）",
      "argumentation": "论证过程（400-600字，详细展开：1.观点背景和行业语境 2.具体数据引用（如有） 3.多维度分析（政策/技术/市场/竞争等） 4.逻辑推演链条 5.对预判的支撑作用）",
      "key_data": ["具体数据1（如：市场规模达X亿，增长率Y%）", "具体数据2", "具体数据3"],
      "logic_steps": ["第一步：前提条件", "第二步：中间推导", "第三步：关键转折", "第四步：得出结论"],
      "enterprise_implication": "对企业{enterprise_profile.get('name', '')}的具体启示（100字以内，结合企业优势给出可执行建议）"
    }}
  ],
  "negative_arguments": [
    {{
      "title": "风险标题（简洁有力）",
      "core_risk": "核心风险（一句话，20字以内）",
      "risk_analysis": "风险深度分析（400-600字，详细展开：1.风险本质和成因 2.历史案例或行业教训 3.风险传导机制 4.可能的影响范围和程度 5.对预判的削弱作用）",
      "risk_indicators": ["风险指标1（如：行业集中度提升X%）", "风险指标2", "风险指标3"],
      "trigger_scenarios": ["触发场景1：具体描述", "触发场景2：具体描述"],
      "enterprise_impact": "对企业{enterprise_profile.get('name', '')}的具体影响（100字以内，结合企业劣势分析）",
      "mitigation": "应对措施（100字以内，给出具体可执行的策略）"
    }}
  ]
}}

**关键要求：**
1. 每个论据的argumentation/risk_analysis必须400-600字，这是报告的核心内容
2. 至少生成3-4个正面论据和3-4个反面论据
3. key_data至少列出3条具体数据
4. logic_steps至少4个步骤
5. 必须结合企业具体情况给出有针对性的分析
6. 如果没有外部参考，基于行业常识进行深入分析"""

        response = await llm_service.generate(prompt, temperature=0.5, max_tokens=5000)
        
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            json_str = response[json_start:json_end]
            
            json_str = json_str.replace('\n', ' ')
            json_str = json_str.replace('\r', ' ')
            
            import re
            json_str = re.sub(r'\s+', ' ', json_str)
            
            arguments = json.loads(json_str)
            
            if "positive_arguments" not in arguments:
                arguments["positive_arguments"] = []
            if "negative_arguments" not in arguments:
                arguments["negative_arguments"] = []
            
            if not arguments["positive_arguments"] or not arguments["negative_arguments"]:
                print("论据为空，使用默认论据")
                default_args = self._get_default_arguments(enterprise_profile)
                if not arguments["positive_arguments"]:
                    arguments["positive_arguments"] = default_args["positive_arguments"]
                if not arguments["negative_arguments"]:
                    arguments["negative_arguments"] = default_args["negative_arguments"]
            
            arguments["search_results"] = search_results
            return arguments
        except Exception as e:
            print(f"解析论据失败: {e}, 使用默认论据")
            default_args = self._get_default_arguments(enterprise_profile)
            default_args["search_results"] = search_results
            return default_args
    
    def _get_default_arguments(self, enterprise_profile: Dict) -> Dict:
        """返回默认论据结构"""
        name = enterprise_profile.get("name", "企业")
        return {
            "positive_arguments": [
                {
                    "title": "市场增长机遇",
                    "core_point": "行业整体呈现增长态势",
                    "argumentation": f"基于行业发展趋势分析，该赛道正处于成长期，市场需求持续扩大。技术进步和消费升级双重驱动下，行业规模稳步增长。政策支持力度加大，为行业发展提供了良好的外部环境。对于处于发展期的企业而言，这提供了良好的市场进入和扩张窗口。建议{name}抓住这一战略机遇期，加快产品迭代和市场拓展步伐。",
                    "key_data": ["行业年复合增长率约15-20%", "市场规模持续扩大", "政策支持力度加大"],
                    "logic_steps": ["市场需求增长", "政策环境优化", "供给能力提升", "企业发展空间打开"],
                    "enterprise_implication": f"建议{name}抓住行业增长红利，加快产品迭代和市场拓展"
                }
            ],
            "negative_arguments": [
                {
                    "title": "竞争压力风险",
                    "core_risk": "市场竞争强度持续上升",
                    "risk_analysis": f"随着市场吸引力提升，新进入者不断涌入，竞争格局日趋激烈。头部企业通过规模效应和品牌优势建立壁垒，新玩家通过差异化策略和资本支持快速切入市场。中小企业面临利润率下降和市场份额被挤压的风险。行业集中度提升可能导致中小企业生存空间收窄。",
                    "risk_indicators": ["行业集中度提升", "价格竞争加剧", "获客成本上升"],
                    "trigger_scenarios": ["资本大量涌入加速竞争", "技术门槛降低带来新进入者"],
                    "enterprise_impact": f"可能导致{name}市场份额受限，利润率下降",
                    "mitigation": "聚焦细分市场，建立差异化竞争优势"
                }
            ]
        }
    
    async def _generate_judgment(
        self, 
        arguments: Dict, 
        session_info: Dict,
        key_insights: Dict,
        enterprise_analysis: Dict
    ) -> Dict[str, Any]:
        """
        生成综合判断（详细版）
        """
        positive_count = len(arguments.get("positive_arguments", []))
        negative_count = len(arguments.get("negative_arguments", []))
        
        enterprise_profile = enterprise_analysis.get("enterprise_profile", {})
        
        prompt = f"""基于以下分析，生成详细综合战略判断。

## 企业概况
- 企业：{enterprise_profile.get('name', '')}（{enterprise_profile.get('stage', '')}阶段）
- 赛道：{enterprise_profile.get('track', '')}

## 正面论据（{positive_count}条）
{json.dumps(arguments.get('positive_arguments', []), ensure_ascii=False, indent=2)}

## 反面论据（{negative_count}条）
{json.dumps(arguments.get('negative_arguments', []), ensure_ascii=False, indent=2)}

请输出以下内容（严格按照JSON格式）：

{{
  "credibility_level": "高/中/低",
  "credibility_score": 75,
  "score_reasoning": "评分理由（150字以内，详细解释为什么给出这个分数）",
  "swot_analysis": {{
    "strengths": ["企业优势1", "企业优势2"],
    "weaknesses": ["企业劣势1", "企业劣势2"],
    "opportunities": ["市场机会1", "市场机会2"],
    "threats": ["潜在威胁1", "潜在威胁2"]
  }},
  "key_variables": [
    {{
      "variable": "变量名称",
      "description": "变量说明（50字以内）",
      "impact": "正向/负向/双向",
      "impact_degree": "高/中/低",
      "monitoring_method": "监测方法（50字以内）",
      "early_warning_signals": ["预警信号1", "预警信号2"]
    }}
  ],
  "scenario_analysis": {{
    "optimistic_scenario": "乐观情景描述及发生概率（80字以内）",
    "baseline_scenario": "基准情景描述及发生概率（80字以内）",
    "pessimistic_scenario": "悲观情景描述及发生概率（80字以内）"
  }},
  "action_suggestions": [
    {{
      "suggestion": "建议内容",
      "rationale": "理由（100字以内）",
      "priority": "高/中/低",
      "timeline": "建议时间",
      "expected_outcome": "预期效果",
      "resource_required": "所需资源"
    }}
  ],
  "risk_mitigation": [
    {{
      "risk": "风险描述",
      "mitigation_strategy": "应对策略",
      "contingency_plan": "应急预案"
    }}
  ],
  "summary": "综合判断总结（400字以内，需包含：1.预判整体评价 2.关键成功因素 3.主要风险提示 4.战略建议方向）"
}}"""

        response = await llm_service.generate(prompt, temperature=0.4, max_tokens=3500)
        
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            json_str = response[json_start:json_end]
            
            json_str = json_str.replace('\n', ' ')
            json_str = json_str.replace('\r', ' ')
            
            import re
            json_str = re.sub(r'\s+', ' ', json_str)
            
            judgment = json.loads(json_str)
            
            required_fields = ["credibility_level", "credibility_score", "key_variables", "action_suggestions", "summary"]
            for field in required_fields:
                if field not in judgment:
                    judgment[field] = self._get_default_judgment().get(field)
            
            return judgment
        except Exception as e:
            print(f"解析综合判断失败: {e}, 使用默认判断")
            return self._get_default_judgment()
    
    def _get_default_judgment(self) -> Dict:
        """返回默认综合判断"""
        return {
            "credibility_level": "中",
            "credibility_score": 50,
            "score_reasoning": "预判存在一定合理性，但面临不确定性因素",
            "swot_analysis": {
                "strengths": ["发展潜力"],
                "weaknesses": ["资源有限"],
                "opportunities": ["市场增长"],
                "threats": ["竞争加剧"]
            },
            "key_variables": [
                {"variable": "市场环境", "description": "宏观经济和行业变化", "impact": "双向", "impact_degree": "中", "monitoring_method": "定期行业报告分析", "early_warning_signals": ["行业增速放缓"]}
            ],
            "scenario_analysis": {
                "optimistic_scenario": "市场快速增长，企业顺利扩张（概率30%）",
                "baseline_scenario": "市场平稳增长，企业稳步发展（概率50%）",
                "pessimistic_scenario": "市场竞争加剧，企业面临挑战（概率20%）"
            },
            "action_suggestions": [
                {"suggestion": "深入市场调研", "rationale": "获取更全面的市场信息", "priority": "高", "timeline": "1-3个月", "expected_outcome": "明确市场定位", "resource_required": "调研团队和预算"}
            ],
            "risk_mitigation": [
                {"risk": "竞争加剧", "mitigation_strategy": "差异化定位", "contingency_plan": "调整产品策略"}
            ],
            "summary": "预判具有一定合理性，建议结合企业实际情况制定灵活战略。关键成功因素包括产品差异化、市场拓展能力和团队执行力。主要风险来自市场竞争和资源约束。建议优先进行市场验证，逐步扩大投入。"
        }
    
    def _format_report(
        self,
        prediction: str,
        arguments: Dict,
        judgment: Dict,
        search_results: Dict,
        key_insights: Dict,
        enterprise_analysis: Dict
    ) -> Dict[str, Any]:
        """
        格式化最终报告
        """
        content = self._build_markdown_report(
            prediction, arguments, judgment, search_results, key_insights, enterprise_analysis
        )
        
        sources = self._extract_valid_sources(search_results)
        
        return {
            "title": "十年战略预判分析报告",
            "content": content,
            "sources": sources
        }
    
    def _build_markdown_report(
        self, 
        prediction: str, 
        arguments: Dict, 
        judgment: Dict,
        search_results: Dict,
        key_insights: Dict,
        enterprise_analysis: Dict
    ) -> str:
        """
        构建Markdown格式报告
        重点：论据分析 > 综合判断 > 企业背景
        """
        sections = []
        
        sections.append("# 十年战略预判分析报告\n")
        
        sections.append("## 一、预判摘要\n")
        sections.append(f"{prediction}\n\n")
        
        sections.append(self._build_enterprise_section_brief(enterprise_analysis))
        
        sections.append("## 三、正面论据分析\n")
        sections.append("*以下论据经过深度论证，是支撑预判成立的核心依据*\n\n")
        
        for i, arg in enumerate(arguments.get("positive_arguments", []), 1):
            sections.append(f"### 3.{i} {arg.get('title', '论据')}\n")
            
            sections.append(f"**核心观点：** {arg.get('core_point', '')}\n\n")
            
            if arg.get('argumentation'):
                sections.append(f"**论证过程：**\n\n{arg.get('argumentation')}\n\n")
            
            if arg.get('key_data'):
                sections.append("**关键数据支撑：**\n")
                for data in arg.get('key_data', []):
                    sections.append(f"- {data}\n")
                sections.append("\n")
            
            if arg.get('logic_steps'):
                sections.append("**逻辑推演步骤：**\n")
                for j, step in enumerate(arg.get('logic_steps', []), 1):
                    sections.append(f"{j}. {step}\n")
                sections.append("\n")
            
            if arg.get('enterprise_implication'):
                sections.append(f"**对企业启示：** {arg.get('enterprise_implication')}\n\n")
            
            sections.append("---\n\n")
        
        sections.append("## 四、反面论据分析\n")
        sections.append("*以下风险经过深度分析，是阻碍预判成立的关键因素*\n\n")
        
        for i, arg in enumerate(arguments.get("negative_arguments", []), 1):
            sections.append(f"### 4.{i} {arg.get('title', '风险')}\n")
            
            sections.append(f"**核心风险：** {arg.get('core_risk', '')}\n\n")
            
            if arg.get('risk_analysis'):
                sections.append(f"**风险深度分析：**\n\n{arg.get('risk_analysis')}\n\n")
            
            if arg.get('risk_indicators'):
                sections.append("**风险指标：**\n")
                for indicator in arg.get('risk_indicators', []):
                    sections.append(f"- {indicator}\n")
                sections.append("\n")
            
            if arg.get('trigger_scenarios'):
                sections.append("**触发场景：**\n")
                for scenario in arg.get('trigger_scenarios', []):
                    sections.append(f"- {scenario}\n")
                sections.append("\n")
            
            if arg.get('enterprise_impact'):
                sections.append(f"**对企业影响：** {arg.get('enterprise_impact')}\n\n")
            
            if arg.get('mitigation'):
                sections.append(f"**应对措施：** {arg.get('mitigation')}\n\n")
            
            sections.append("---\n\n")
        
        sections.append("## 五、综合判断\n")
        
        sections.append("### 5.1 预判可信度评估\n")
        sections.append(f"**可信度等级：** {judgment.get('credibility_level', '中')}\n\n")
        sections.append(f"**可信度评分：** {judgment.get('credibility_score', 50)}/100\n\n")
        if judgment.get('score_reasoning'):
            sections.append(f"**评分理由：** {judgment.get('score_reasoning')}\n\n")
        
        swot = judgment.get("swot_analysis", {})
        if swot:
            sections.append("### 5.2 SWOT分析\n\n")
            sections.append(f"**优势（Strengths）：** {', '.join(swot.get('strengths', []))}\n\n")
            sections.append(f"**劣势（Weaknesses）：** {', '.join(swot.get('weaknesses', []))}\n\n")
            sections.append(f"**机会（Opportunities）：** {', '.join(swot.get('opportunities', []))}\n\n")
            sections.append(f"**威胁（Threats）：** {', '.join(swot.get('threats', []))}\n\n")
        
        sections.append("### 5.3 关键变量识别\n\n")
        for var in judgment.get("key_variables", []):
            if isinstance(var, dict):
                sections.append(f"**{var.get('variable', '')}**\n")
                sections.append(f"- 说明：{var.get('description', '')}\n")
                sections.append(f"- 影响方向：{var.get('impact', '')}（影响程度：{var.get('impact_degree', '中')}）\n")
                sections.append(f"- 监测方法：{var.get('monitoring_method', '')}\n")
                if var.get('early_warning_signals'):
                    sections.append(f"- 预警信号：{', '.join(var.get('early_warning_signals', []))}\n")
                sections.append("\n")
        
        scenario = judgment.get("scenario_analysis", {})
        if scenario:
            sections.append("### 5.4 情景分析\n\n")
            sections.append(f"**乐观情景：** {scenario.get('optimistic_scenario', '')}\n\n")
            sections.append(f"**基准情景：** {scenario.get('baseline_scenario', '')}\n\n")
            sections.append(f"**悲观情景：** {scenario.get('pessimistic_scenario', '')}\n\n")
        
        sections.append("### 5.5 行动建议\n\n")
        for i, sug in enumerate(judgment.get("action_suggestions", []), 1):
            if isinstance(sug, dict):
                sections.append(f"**建议{i}：{sug.get('suggestion', '')}**\n")
                sections.append(f"- 理由：{sug.get('rationale', '')}\n")
                sections.append(f"- 优先级：{sug.get('priority', '')}\n")
                sections.append(f"- 建议时间：{sug.get('timeline', '')}\n")
                if sug.get('expected_outcome'):
                    sections.append(f"- 预期效果：{sug.get('expected_outcome', '')}\n")
                if sug.get('resource_required'):
                    sections.append(f"- 所需资源：{sug.get('resource_required', '')}\n")
                sections.append("\n")
        
        risk_mitigation = judgment.get("risk_mitigation", [])
        if risk_mitigation:
            sections.append("### 5.6 风险应对策略\n\n")
            for i, rm in enumerate(risk_mitigation, 1):
                sections.append(f"**风险{i}：{rm.get('risk', '')}**\n")
                sections.append(f"- 应对策略：{rm.get('mitigation_strategy', '')}\n")
                sections.append(f"- 应急预案：{rm.get('contingency_plan', '')}\n\n")
        
        sections.append("### 5.7 综合判断总结\n\n")
        sections.append(f"{judgment.get('summary', '')}\n")
        
        valid_sources = self._extract_valid_sources(search_results)
        if valid_sources:
            sections.append("\n## 六、参考信源\n\n")
            for source in valid_sources:
                sections.append(f"- [{source['title']}]({source['url']})\n")
        
        return "\n".join(sections)
    
    def _build_enterprise_section_brief(self, enterprise_analysis: Dict) -> str:
        """
        构建企业背景分析部分（精简版）
        """
        sections = []
        sections.append("## 二、企业背景概览\n")
        
        profile = enterprise_analysis.get("enterprise_profile", {})
        sections.append(f"**企业名称：** {profile.get('name', '未提供')}\n")
        sections.append(f"**所属行业：** {profile.get('industry', '未提供')}\n")
        sections.append(f"**发展阶段：** {profile.get('stage', '未提供')}\n")
        sections.append(f"**选定赛道：** {profile.get('track', '未提供')}\n\n")
        
        sections.append(f"**资源概况：** {enterprise_analysis.get('resource_summary', '未评估')}\n\n")
        
        core_advantages = enterprise_analysis.get("core_advantages", [])
        if core_advantages:
            sections.append(f"**核心优势：** {', '.join(core_advantages)}\n\n")
        
        core_disadvantages = enterprise_analysis.get("core_disadvantages", [])
        if core_disadvantages:
            sections.append(f"**核心劣势：** {', '.join(core_disadvantages)}\n\n")
        
        sections.append(f"**战略定位：** {enterprise_analysis.get('strategic_position', '未评估')}\n\n")
        
        sections.append("---\n\n")
        
        return "\n".join(sections)
    
    def _format_search_results_with_links(self, results: List[Dict]) -> str:
        """格式化搜索结果 - 只包含有链接的"""
        formatted = []
        for i, r in enumerate(results[:6], 1):
            title = r.get('title', '')
            snippet = r.get('snippet', '')
            link = r.get('link', '')
            if link and link.startswith('http'):
                formatted.append(f"{i}. 【{title}】\n   摘要：{snippet[:150]}\n   链接：{link}\n")
        return "\n".join(formatted) if formatted else "无有效外部参考信息"
    
    def _extract_valid_sources(self, search_results: Dict) -> List[Dict]:
        """提取有效的信源 - 只包含有真实链接的"""
        sources = []
        seen_urls = set()
        
        for result in search_results.get("supporting", []) + search_results.get("opposing", []):
            url = result.get("link", "")
            if url and url.startswith("http") and url not in seen_urls:
                sources.append({
                    "title": result.get("title", ""),
                    "url": url
                })
                seen_urls.add(url)
        
        return sources[:8]

ten_year_agent = TenYearAgent()
