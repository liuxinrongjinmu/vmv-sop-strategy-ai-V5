from typing import Dict, Any, List
import asyncio
import json
import re
from app.services.llm import llm_service
from app.services.search import search_service

class TenYearAgent:
    """
    十年战略Agent
    负责赛道预判分析，生成正反论据和综合判断
    """
    
    def __init__(self):
        self.name = "ten_year_strategy"
    
    async def analyze(self, prediction: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行十年战略分析（优化版：并行化+降低tokens）
        """
        session_info = context.get("session_info", {})
        chat_history = context.get("chat_history", [])
        uploaded_files = context.get("uploaded_files", [])
        
        print("[TenYearAgent] 开始分析...")
        print(f"[TenYearAgent] 预测内容: {prediction[:100]}...")
        
        print("[TenYearAgent] [并行] 提取关键洞察 + 分析企业背景 + 提取假设...")
        key_insights_task = self._extract_key_insights(chat_history, uploaded_files, session_info)
        enterprise_task = self._analyze_enterprise(session_info, {})
        
        key_insights, enterprise_analysis = await asyncio.gather(
            key_insights_task, enterprise_task
        )
        
        assumptions = await self._extract_assumptions(prediction, {}, enterprise_analysis)
        print(f"[TenYearAgent] 并行步骤完成: {len(assumptions)}个假设")
        
        print("[TenYearAgent] 搜索证据...")
        search_results = await self._search_evidence(assumptions, session_info, prediction)
        print(f"[TenYearAgent] 证据搜索完成: 支持{len(search_results['supporting'])}条, 反对{len(search_results['opposing'])}条")
        
        print("[TenYearAgent] 构建论据...")
        arguments = await self._build_arguments(
            prediction, assumptions, search_results, session_info, enterprise_analysis
        )
        print(f"[TenYearAgent] 论据构建完成: 正面{len(arguments.get('positive_arguments', []))}条, 反面{len(arguments.get('negative_arguments', []))}条")
        
        print("[TenYearAgent] 生成综合判断...")
        judgment = await self._generate_judgment(arguments, enterprise_analysis)
        print(f"[TenYearAgent] 综合判断生成完成")
        
        print("[TenYearAgent] 格式化报告...")
        report = self._format_report(prediction, arguments, judgment)
        print(f"[TenYearAgent] 报告生成完成: 内容长度{len(report['content'])}字符")
        
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
                for msg in chat_history[-15:]
            ])
            
            prompt = f"""从对话中提取关键信息（JSON格式）：

{chat_text[:2000]}

输出JSON：
{{"summary":"100字总结","key_decisions":["决策1"],"concerns":["担忧1"],"opportunities":["机会1"],"mentioned_resources":["资源1"],"mentioned_advantages":["优势1"],"mentioned_challenges":["挑战1"]}}"""
            
            try:
                response = await llm_service.generate(prompt, temperature=0.3, max_tokens=600)
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
        
        for file_info in uploaded_files[:2]:
            filename = file_info.get("filename", "")
            content = file_info.get("content", "")
            
            if content:
                prompt = f"""从文件中提取关键信息（JSON格式）：
文件名：{filename}
内容：{content[:1200]}

输出JSON：{{"filename":"{filename}","main_topic":"主题","key_data":["数据1"]}}"""
                
                try:
                    response = await llm_service.generate(prompt, temperature=0.3, max_tokens=400)
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
        prompt = f"""对企业进行简要分析（JSON格式）：
- 企业：{session_info.get('company_name', '未提供')}
- 行业：{session_info.get('industry', '未提供')}
- 阶段：{session_info.get('stage', '未提供')}
- 规模：{session_info.get('team_size', '未提供')}
- 赛道：{session_info.get('selected_track', '未提供')}
- 愿景：{session_info.get('vision', '未提供')[:50]}
- 使命：{session_info.get('mission', '未提供')[:50]}
- 补充：{session_info.get('additional_info', '未提供')[:100]}

输出JSON：
{{"enterprise_profile":{{"name":"企业名","industry":"行业","stage":"阶段","track":"赛道"}},"resource_summary":"80字资源概况","core_advantages":["优势1","优势2"],"core_disadvantages":["劣势1","劣势2"],"strategic_position":"50字定位"}}"""

        try:
            response = await llm_service.generate(prompt, temperature=0.3, max_tokens=500)
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            return json.loads(response[json_start:json_end])
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
        
        prompt = f"""从预判中提取4-5个关键假设（每行一个，不要编号）：

预判：{prediction[:300]}
企业：{enterprise_profile.get('name', '')}（{enterprise_profile.get('track', '')}）

关键假设："""
        
        response = await llm_service.generate(prompt, temperature=0.3, max_tokens=400)
        assumptions = [line.strip() for line in response.split("\n") if line.strip()]
        return assumptions[:5]
    
    async def _search_evidence(
        self, 
        assumptions: List[str], 
        session_info: Dict,
        prediction: str = ""
    ) -> Dict[str, List]:
        """
        搜索支持/反对假设的证据（优化：减少搜索次数）
        """
        results = {"supporting": [], "opposing": []}
        
        track = session_info.get("selected_track", "")
        industry = session_info.get("industry", "")
        keywords = (prediction[:80] + " " + track + " " + industry).strip()
        
        try:
            support_query = f"{keywords} 市场分析 发展趋势 增长"
            print(f"[Search] 支持性搜索: {support_query[:60]}...")
            support_results = await search_service.search(support_query, 5)
            for r in support_results:
                if r.get("link", "").startswith("http"):
                    results["supporting"].append(r)
            
            oppose_query = f"{keywords} 风险 挑战 竞争"
            print(f"[Search] 反对性搜索: {oppose_query[:60]}...")
            oppose_results = await search_service.search(oppose_query, 5)
            for r in oppose_results:
                if r.get("link", "").startswith("http"):
                    results["opposing"].append(r)
                        
        except Exception as e:
            print(f"搜索服务调用失败: {e}")
        
        seen_urls = set()
        results["supporting"] = [r for r in results["supporting"] if r["link"] not in seen_urls and not seen_urls.add(r["link"])][:6]
        seen_urls.clear()
        results["opposing"] = [r for r in results["opposing"] if r["link"] not in seen_urls and not seen_urls.add(r["link"])][:6]
        
        print(f"[Search] 最终结果: 支持{len(results['supporting'])}条, 反对{len(results['opposing'])}条")
        return results
    
    async def _build_arguments(
        self,
        prediction: str,
        assumptions: List[str],
        search_results: Dict,
        session_info: Dict,
        enterprise_analysis: Dict
    ) -> Dict[str, List]:
        """
        构建正反论据（优化版：降低tokens+简化prompt）
        """
        supporting_text = self._format_search_results(search_results["supporting"][:4])
        opposing_text = self._format_search_results(search_results["opposing"][:4])
        
        enterprise_profile = enterprise_analysis.get("enterprise_profile", {})
        name = enterprise_profile.get('name', '企业')
        
        prompt = f"""作为战略咨询顾问，基于以下信息构建正反论据。

## 企业
{name}（{enterprise_profile.get('stage', '')}阶段），行业：{enterprise_profile.get('industry', '')}，赛道：{enterprise_profile.get('track', '')}
优势：{', '.join(enterprise_analysis.get('core_advantages', []) or ['待建立'])}
劣势：{', '.join(enterprise_analysis.get('core_disadvantages', []) or ['待改善'])}

## 预判
{prediction[:400]}

## 假设
{chr(10).join(f'- {a}' for a in assumptions)}

## 参考信息
支持：{supporting_text or "无"}
反对：{opposing_text or "无"}

输出JSON（每个argumentation/risk_analysis 250-400字）：
{{
  "positive_arguments": [
    {{"title":"标题","core_point":"核心观点20字内","argumentation":"论证250-400字","key_data":["数据1","数据2","data3"],"logic_steps":["步骤1","步骤2","步骤3","步骤4"],"enterprise_implication":"企业启示80字内"}}
  ],
  "negative_arguments": [
    {{"title":"风险标题","core_risk":"核心风险20字内","risk_analysis":"风险分析250-400字","risk_indicators":["指标1","指标2","指标3"],"trigger_scenarios":["场景1","场景2"],"enterprise_impact":"企业影响80字内","mitigation":"应对措施80字内"}}
  ]
}}

要求：各2-3条论据，结合企业具体情况。"""

        response = await llm_service.generate(prompt, temperature=0.5, max_tokens=3000)
        
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            json_str = re.sub(r'\s+', ' ', response[json_start:json_end])
            arguments = json.loads(json_str)
            
            if "positive_arguments" not in arguments:
                arguments["positive_arguments"] = []
            if "negative_arguments" not in arguments:
                arguments["negative_arguments"] = []
            
            if not arguments["positive_arguments"] or not arguments["negative_arguments"]:
                default_args = self._get_default_arguments(name)
                if not arguments["positive_arguments"]:
                    arguments["positive_arguments"] = default_args["positive_arguments"]
                if not arguments["negative_arguments"]:
                    arguments["negative_arguments"] = default_args["negative_arguments"]
            
            return arguments
        except Exception as e:
            print(f"解析论据失败: {e}, 使用默认论据")
            return self._get_default_arguments(name)
    
    def _get_default_arguments(self, name: str) -> Dict:
        """返回默认论据结构"""
        return {
            "positive_arguments": [
                {"title": "市场增长机遇", "core_point": "行业整体呈现增长态势",
                 "argumentation": f"该赛道正处于成长期，市场需求持续扩大。技术进步和消费升级双重驱动下，行业规模稳步增长。政策支持力度加大，为行业发展提供了良好外部环境。建议{name}抓住这一战略机遇期。",
                 "key_data": ["行业年复合增长率约15-20%", "市场规模持续扩大", "政策支持力度加大"],
                 "logic_steps": ["市场需求增长", "政策环境优化", "供给能力提升", "企业发展空间打开"],
                 "enterprise_implication": f"建议{name}抓住行业增长红利"},
            ],
            "negative_arguments": [
                {"title": "竞争压力风险", "core_risk": "市场竞争强度持续上升",
                 "risk_analysis": f"随着市场吸引力提升，新进入者不断涌入，竞争格局日趋激烈。头部企业通过规模效应建立壁垒，中小企业面临利润率下降风险。",
                 "risk_indicators": ["行业集中度提升", "价格竞争加剧", "获客成本上升"],
                 "trigger_scenarios": ["资本大量涌入加速竞争", "技术门槛降低带来新进入者"],
                 "enterprise_impact": f"可能导致{name}市场份额受限", "mitigation": "聚焦细分市场建立差异化"}
            ]
        }
    
    async def _generate_judgment(
        self, 
        arguments: Dict, 
        enterprise_analysis: Dict
    ) -> Dict[str, Any]:
        """
        生成综合判断（优化版）
        """
        enterprise_profile = enterprise_analysis.get("enterprise_profile", {})
        name = enterprise_profile.get('name', '')
        
        pos_args = json.dumps(arguments.get('positive_arguments', []), ensure_ascii=False)[:1500]
        neg_args = json.dumps(arguments.get('negative_arguments', []), ensure_ascii=False)[:1500]
        
        prompt = f"""基于以下论据生成综合判断（JSON格式）：

企业：{name}（{enterprise_profile.get('track', '')}）

正面论据：{pos_args}
反面论据：{neg_args}

输出JSON：
{{
  "credibility_level":"高/中/低",
  "credibility_score":75,
  "score_reasoning":"评分理由100字内",
  "swot_analysis":{{"strengths":["优势1","优势2"],"weaknesses":["劣势1"],"opportunities":["机会1"],"threats":["威胁1"]}},
  "key_variables":[{{"variable":"变量名","description":"说明40字内","impact":"正向/负向","impact_degree":"高/中/低","monitoring_method":"监测方法40字内"}}],
  "scenario_analysis":{{"optimistic_scenario":"乐观情景60字内","baseline_scenario":"基准情景60字内","pessimistic_scenario":"悲观情景60字内"}},
  "action_suggestions":[{{"suggestion":"建议","rationale":"理由80字内","priority":"高/中/低","timeline":"时间"}}],
  "risk_mitigation":[{{"risk":"风险","mitigation_strategy":"策略","contingency_plan":"预案"}}],
  "summary":"总结300字内：整体评价+成功因素+风险提示+战略方向"
}}"""

        response = await llm_service.generate(prompt, temperature=0.4, max_tokens=2000)
        
        try:
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            json_str = re.sub(r'\s+', ' ', response[json_start:json_end])
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
            "swot_analysis": {"strengths": ["发展潜力"], "weaknesses": ["资源有限"], "opportunities": ["市场增长"], "threats": ["竞争加剧"]},
            "key_variables": [{"variable": "市场环境", "description": "宏观经济和行业变化", "impact": "双向", "impact_degree": "中", "monitoring_method": "定期行业报告分析"}],
            "scenario_analysis": {"optimistic_scenario": "市场快速增长（概率30%）", "baseline_scenario": "市场平稳增长（概率50%）", "pessimistic_scenario": "竞争加剧（概率20%）"},
            "action_suggestions": [{"suggestion": "深入市场调研", "rationale": "获取更全面的市场信息", "priority": "高", "timeline": "1-3个月"}],
            "risk_mitigation": [{"risk": "竞争加剧", "mitigation_strategy": "差异化定位", "contingency_plan": "调整产品策略"}],
            "summary": "预判具有一定合理性，建议结合实际情况制定灵活战略。关键成功因素包括产品差异化和市场拓展能力。主要风险来自市场竞争和资源约束。"
        }
    
    def _format_report(
        self,
        prediction: str,
        arguments: Dict,
        judgment: Dict
    ) -> Dict[str, Any]:
        """
        格式化最终报告
        """
        content = self._build_markdown_report(prediction, arguments, judgment)
        
        return {
            "title": "十年战略预判分析报告",
            "content": content,
            "sources": []
        }
    
    def _build_markdown_report(
        self, 
        prediction: str, 
        arguments: Dict, 
        judgment: Dict
    ) -> str:
        """
        构建Markdown格式报告
        """
        sections = []
        
        sections.append("# 十年战略预判分析报告\n")
        sections.append("## 一、预判摘要\n")
        sections.append(f"{prediction}\n\n")
        
        sections.append("## 二、正面论据分析\n")
        for i, arg in enumerate(arguments.get("positive_arguments", []), 1):
            sections.append(f"### 2.{i} {arg.get('title', '论据')}\n")
            sections.append(f"**核心观点：** {arg.get('core_point', '')}\n\n")
            if arg.get('argumentation'):
                sections.append(f"**论证过程：**\n\n{arg.get('argumentation')}\n\n")
            if arg.get('key_data'):
                sections.append("**关键数据支撑：**\n" + "\n".join(f"- {d}" for d in arg.get('key_data', [])) + "\n\n")
            if arg.get('logic_steps'):
                sections.append("**逻辑推演步骤：**\n" + "\n".join(f"{j}. {s}" for j, s in enumerate(arg.get('logic_steps', []), 1)) + "\n\n")
            if arg.get('enterprise_implication'):
                sections.append(f"**对企业启示：** {arg.get('enterprise_implication')}\n\n---\n\n")
        
        sections.append("## 三、反面论据分析\n")
        for i, arg in enumerate(arguments.get("negative_arguments", []), 1):
            sections.append(f"### 3.{i} {arg.get('title', '风险')}\n")
            sections.append(f"**核心风险：** {arg.get('core_risk', '')}\n\n")
            if arg.get('risk_analysis'):
                sections.append(f"**风险深度分析：**\n\n{arg.get('risk_analysis')}\n\n")
            if arg.get('risk_indicators'):
                sections.append("**风险指标：**\n" + "\n".join(f"- {d}" for d in arg.get('risk_indicators', [])) + "\n\n")
            if arg.get('enterprise_impact'):
                sections.append(f"**对企业影响：** {arg.get('enterprise_impact')}\n")
            if arg.get('mitigation'):
                sections.append(f"**应对措施：** {arg.get('mitigation')}\n---\n\n")
        
        sections.append("## 四、综合判断\n")
        sections.append(f"### 4.1 可信度评估\n**等级：** {judgment.get('credibility_level', '中')} | **评分：** {judgment.get('credibility_score', 50)}/100\n\n")
        if judgment.get('score_reasoning'):
            sections.append(f"**理由：** {judgment.get('score_reasoning')}\n\n")
        
        swot = judgment.get("swot_analysis", {})
        if swot:
            sections.append("### 4.2 SWOT分析\n\n")
            sections.append(f"- **优势：** {', '.join(swot.get('strengths', []))}\n")
            sections.append(f"- **劣势：** {', '.join(swot.get('weaknesses', []))}\n")
            sections.append(f"- **机会：** {', '.join(swot.get('opportunities', []))}\n")
            sections.append(f"- **威胁：** {', '.join(swot.get('threats', []))}\n\n")
        
        sections.append("### 4.3 关键变量识别\n\n")
        for var in judgment.get("key_variables", []):
            if isinstance(var, dict):
                sections.append(f"**{var.get('variable', '')}** - {var.get('description', '')}（影响：{var.get('impact', '')}/{var.get('impact_degree', '中')}）\n")
        
        scenario = judgment.get("scenario_analysis", {})
        if scenario:
            sections.append("\n### 4.4 情景分析\n\n")
            sections.append(f"- **乐观：** {scenario.get('optimistic_scenario', '')}\n")
            sections.append(f"- **基准：** {scenario.get('baseline_scenario', '')}\n")
            sections.append(f"- **悲观：** {scenario.get('pessimistic_scenario', '')}\n\n")
        
        sections.append("### 4.5 行动建议\n\n")
        for i, sug in enumerate(judgment.get("action_suggestions", []), 1):
            if isinstance(sug, dict):
                sections.append(f"**建议{i}: {sug.get('suggestion', '')}** - 理由：{sug.get('rationale', '')} | 优先级：{sug.get('priority', '')} | 时间：{sug.get('timeline', '')}\n\n")
        
        rm_list = judgment.get("risk_mitigation", [])
        if rm_list:
            sections.append("### 4.6 风险应对策略\n\n")
            for i, rm in enumerate(rm_list, 1):
                sections.append(f"**风险{i}: {rm.get('risk', '')}** - 应对：{rm.get('mitigation_strategy', '')} | 预案：{rm.get('contingency_plan', '')}\n\n")
        
        sections.append("### 4.7 综合判断总结\n\n")
        sections.append(f"{judgment.get('summary', '')}\n")
        
        return "\n".join(sections)
    
    def _format_search_results(self, results: List[Dict]) -> str:
        """格式化搜索结果（精简版）"""
        formatted = []
        for i, r in enumerate(results[:4], 1):
            title = r.get('title', '')
            snippet = r.get('snippet', '')[:100]
            link = r.get('link', '')
            if link.startswith("http"):
                formatted.append(f"{i}. 【{title}】{snippet}")
        return "\n".join(formatted) if formatted else ""

ten_year_agent = TenYearAgent()
