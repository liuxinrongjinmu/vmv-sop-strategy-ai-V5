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
        import time
        start_time = time.time()
        
        session_info = context.get("session_info", {})
        chat_history = context.get("chat_history", [])
        uploaded_files = context.get("uploaded_files", [])
        
        print("[TenYearAgent] 开始分析...")
        print(f"[TenYearAgent] 预测内容: {prediction[:100]}...")
        
        print("[TenYearAgent] [并行] 提取关键洞察 + 分析企业背景 + 提取假设...")
        key_insights_task = self._extract_key_insights(chat_history, uploaded_files, session_info)
        enterprise_task = self._analyze_enterprise(session_info, {})
        
        step1_start = time.time()
        key_insights, enterprise_analysis = await asyncio.gather(
            key_insights_task, enterprise_task
        )
        step1_end = time.time()
        print(f"[TenYearAgent] 并行步骤完成, 耗时: {step1_end - step1_start:.2f}秒")
        
        step2_start = time.time()
        assumptions = await self._extract_assumptions(prediction, {}, enterprise_analysis)
        step2_end = time.time()
        print(f"[TenYearAgent] 提取假设完成: {len(assumptions)}个假设, 耗时: {step2_end - step2_start:.2f}秒")
        
        step3_start = time.time()
        print("[TenYearAgent] 搜索证据...")
        search_results = await self._search_evidence(assumptions, session_info, prediction)
        step3_end = time.time()
        print(f"[TenYearAgent] 证据搜索完成: 支持{len(search_results['supporting'])}条, 反对{len(search_results['opposing'])}条, 耗时: {step3_end - step3_start:.2f}秒")
        
        step4_start = time.time()
        print("[TenYearAgent] 构建论据...")
        arguments = await self._build_arguments(
            prediction, assumptions, search_results, session_info, enterprise_analysis
        )
        step4_end = time.time()
        print(f"[TenYearAgent] 论据构建完成: 正面{len(arguments.get('positive_arguments', []))}条, 反面{len(arguments.get('negative_arguments', []))}条, 耗时: {step4_end - step4_start:.2f}秒")
        
        step5_start = time.time()
        print("[TenYearAgent] 生成综合判断...")
        judgment = await self._generate_judgment(arguments, enterprise_analysis)
        step5_end = time.time()
        print(f"[TenYearAgent] 综合判断生成完成, 耗时: {step5_end - step5_start:.2f}秒")
        
        step6_start = time.time()
        print("[TenYearAgent] 格式化报告...")
        report = self._format_report(prediction, arguments, judgment)
        step6_end = time.time()
        print(f"[TenYearAgent] 报告生成完成: 内容长度{len(report['content'])}字符, 耗时: {step6_end - step6_start:.2f}秒")
        
        total_time = time.time() - start_time
        print(f"[TenYearAgent] 总耗时: {total_time:.2f}秒")
        
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
        分析企业背景（增强版：基于事实数据）
        """
        company_name = session_info.get('company_name', '未提供')
        industry = session_info.get('industry', '未提供')
        stage = session_info.get('stage', '未提供')
        track = session_info.get('selected_track', '未提供')
        additional_info = session_info.get('additional_info', '未提供')
        
        # 基于实际信息生成分析，避免臆测
        prompt = f"""对企业进行分析（JSON格式），严格基于以下事实信息，不要臆测：
- 企业：{company_name}
- 行业：{industry}
- 阶段：{stage}
- 赛道：{track}
- 补充信息：{additional_info[:200]}

输出JSON，只包含基于上述信息的分析：
{{"enterprise_profile":{{"name":"{company_name}","industry":"{industry}","stage":"{stage}","track":"{track}"}},"resource_summary":"80字资源概况（基于已知信息）","core_advantages":["基于已知信息的优势1","基于已知信息的优势2"],"core_disadvantages":["基于已知信息的劣势1","基于已知信息的劣势2"],"strategic_position":"50字定位（基于已知信息）"}}"""

        try:
            response = await llm_service.generate(prompt, temperature=0.2, max_tokens=500)
            json_start = response.find("{")
            json_end = response.rfind("}") + 1
            analysis = json.loads(response[json_start:json_end])
            
            # 确保输出包含必要字段
            if "core_advantages" in analysis and not analysis["core_advantages"]:
                analysis["core_advantages"] = ["需要更多企业信息"]
            if "core_disadvantages" in analysis and not analysis["core_disadvantages"]:
                analysis["core_disadvantages"] = ["需要更多企业信息"]
                
            return analysis
        except Exception as e:
            print(f"企业分析失败: {e}")
            return {
                "enterprise_profile": {
                    "name": company_name,
                    "industry": industry,
                    "stage": stage,
                    "track": track
                },
                "resource_summary": "基于有限信息，企业资源状况需要进一步确认",
                "core_advantages": ["需要更多企业信息"],
                "core_disadvantages": ["需要更多企业信息"],
                "strategic_position": "基于有限信息，战略定位需要进一步确认"
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
            # 只执行一次搜索，同时获取支持和反对的信息
            combined_query = f"{keywords} 市场分析 发展趋势 增长 风险 挑战 竞争"
            print(f"[Search] 综合搜索: {combined_query[:60]}...")
            combined_results = await search_service.search(combined_query, 8)
            
            # 简单分类结果
            for r in combined_results:
                if r.get("link", "").startswith("http"):
                    # 根据标题和摘要简单分类
                    text = (r.get("title", "") + " " + r.get("snippet", "")).lower()
                    if any(word in text for word in ["增长", "趋势", "机遇", "发展", "市场"]):
                        results["supporting"].append(r)
                    else:
                        results["opposing"].append(r)
                        
        except Exception as e:
            print(f"搜索服务调用失败: {e}")
        
        seen_urls = set()
        results["supporting"] = [r for r in results["supporting"] if r["link"] not in seen_urls and not seen_urls.add(r["link"])][:4]
        seen_urls.clear()
        results["opposing"] = [r for r in results["opposing"] if r["link"] not in seen_urls and not seen_urls.add(r["link"])][:4]
        
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
        构建正反论据（基于事实和数据）
        """
        supporting_text = self._format_search_results(search_results["supporting"][:4])
        opposing_text = self._format_search_results(search_results["opposing"][:4])
        
        enterprise_profile = enterprise_analysis.get("enterprise_profile", {})
        name = enterprise_profile.get('name', '企业')
        industry = enterprise_profile.get('industry', '未提供')
        track = enterprise_profile.get('track', '未提供')
        stage = enterprise_profile.get('stage', '未提供')
        
        advantages = enterprise_analysis.get('core_advantages', [])
        disadvantages = enterprise_analysis.get('core_disadvantages', [])
        
        prompt = f"""作为战略咨询顾问，基于以下事实信息构建正反论据。

## 企业事实信息
企业：{name}
行业：{industry}
阶段：{stage}
赛道：{track}
已知优势：{', '.join(advantages) or '需要更多信息'}
已知劣势：{', '.join(disadvantages) or '需要更多信息'}

## 预判
{prediction[:300]}

## 关键假设
{chr(10).join(f'- {a}' for a in assumptions[:4])}

## 市场数据和参考信息
支持性信息：
{supporting_text or "无具体数据支持"}

反对性信息：
{opposing_text or "无具体数据支持"}

## 重要要求
1. 所有分析结论必须基于上述事实信息和数据，不得臆测
2. 对关键结论必须提供数据支持或明确标注为假设
3. 避免基于企业名称的臆测
4. 当信息不足时，明确标注为"基于有限信息的分析"

输出JSON（每个方向2-3个论据，内容深入）：
{
  "positive_arguments": [
    {"title":"标题","core_point":"核心观点20字内","argumentation":"论证200-250字，包含数据支持","key_data":["数据1","数据2"],"logic_steps":["步骤1","步骤2","步骤3"],"enterprise_implication":"企业启示60字内"}
  ],
  "negative_arguments": [
    {"title":"风险标题","core_risk":"核心风险20字内","risk_analysis":"风险分析200-250字，包含数据支持","risk_indicators":["指标1","指标2"],"enterprise_impact":"企业影响60字内","mitigation":"应对措施60字内"}
  ]
}

要求：严格基于事实信息，避免臆测，每个结论都要有数据支持或明确标注为假设。"""

        response = await llm_service.generate(prompt, temperature=0.4, max_tokens=3000)
        
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
        
        pos_args = json.dumps(arguments.get('positive_arguments', [])[:3], ensure_ascii=False)[:1200]
        neg_args = json.dumps(arguments.get('negative_arguments', [])[:3], ensure_ascii=False)[:1200]
        
        prompt = f"""基于以下论据生成综合判断（JSON格式）：

企业：{name}（{enterprise_profile.get('track', '')}）

正面论据：{pos_args}
反面论据：{neg_args}

输出JSON（内容深入，重点突出）：
{
  "credibility_level":"高/中/低",
  "credibility_score":75,
  "score_reasoning":"评分理由80字内",
  "swot_analysis":{"strengths":["优势"],"weaknesses":["劣势"],"opportunities":["机会"],"threats":["威胁"]},
  "key_variables":[{"variable":"变量名","description":"说明25字内","impact":"正向/负向","impact_degree":"高/中/低","monitoring_method":"监测方法25字内"}],
  "scenario_analysis":{"optimistic_scenario":"乐观情景40字内","baseline_scenario":"基准情景40字内","pessimistic_scenario":"悲观情景40字内"},
  "action_suggestions":[{"suggestion":"建议","rationale":"理由50字内","priority":"高/中/低","timeline":"时间"}],
  "risk_mitigation":[{"risk":"风险","mitigation_strategy":"策略","contingency_plan":"预案"}],
  "summary":"总结200字内：整体评价+成功因素+风险提示+战略方向"
}

要求：内容深入，重点突出，不要重复。"""

        response = await llm_service.generate(prompt, temperature=0.4, max_tokens=1800)
        
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
        sections.append(f"{prediction}\n\n---\n\n")
        
        sections.append("## 二、正面论据分析\n")
        for i, arg in enumerate(arguments.get("positive_arguments", []), 1):
            sections.append(f"### 2.{i} {arg.get('title', '论据')}\n")
            sections.append(f"**核心观点：** {arg.get('core_point', '')}\n\n")
            if arg.get('argumentation'):
                sections.append(f"**论证过程：**\n\n{arg.get('argumentation')}\n\n")
            if arg.get('key_data'):
                sections.append("**数据支持：**\n" + "\n".join(f"- {d}" for d in arg.get('key_data', [])) + "\n\n")
            if arg.get('logic_steps'):
                sections.append("**逻辑推演步骤：**\n" + "\n".join(f"{j}. {s}" for j, s in enumerate(arg.get('logic_steps', []), 1)) + "\n\n")
            if arg.get('enterprise_implication'):
                sections.append(f"**对企业启示：** {arg.get('enterprise_implication')}\n\n")
        
        sections.append("---\n\n")
        
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
                sections.append(f"**应对措施：** {arg.get('mitigation')}\n\n")
        
        sections.append("---\n\n")
        
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
        
        key_vars = judgment.get("key_variables", [])
        if key_vars:
            sections.append("### 4.3 关键变量识别\n\n")
            for var in key_vars:
                if isinstance(var, dict):
                    sections.append(f"**{var.get('variable', '')}** - {var.get('description', '')}（影响：{var.get('impact', '')}/{var.get('impact_degree', '中')}）\n")
            sections.append("\n")
        
        scenario = judgment.get("scenario_analysis", {})
        if scenario:
            sections.append("### 4.4 情景分析\n\n")
            sections.append(f"- **乐观：** {scenario.get('optimistic_scenario', '')}\n")
            sections.append(f"- **基准：** {scenario.get('baseline_scenario', '')}\n")
            sections.append(f"- **悲观：** {scenario.get('pessimistic_scenario', '')}\n\n")
        
        suggestions = judgment.get("action_suggestions", [])
        if suggestions:
            sections.append("### 4.5 行动建议\n\n")
            for i, sug in enumerate(suggestions, 1):
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