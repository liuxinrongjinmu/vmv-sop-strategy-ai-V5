from typing import Dict, Any, Optional, List
from app.services.llm import llm_service
from app.agents.ten_year import ten_year_agent

class OrchestratorAgent:
    """
    总控Agent
    负责调度和协调其他Agent，维护会话状态
    """
    
    def __init__(self):
        self.name = "orchestrator"
    
    async def process_message(
        self,
        message: str,
        session_info: Dict[str, Any],
        current_stage: int,
        uploaded_files: List[Dict] = None,
        chat_history: List[Dict] = None
    ) -> Dict[str, Any]:
        
        if uploaded_files is None:
            uploaded_files = []
        if chat_history is None:
            chat_history = []
            
        intent = await self._detect_intent(message, current_stage)
        
        if intent == "generate_report":
            return await self._handle_report_generation(message, session_info, uploaded_files)
        elif intent == "stage_transition":
            return await self._handle_stage_transition(current_stage)
        else:
            return await self._handle_general_chat(message, session_info, current_stage, uploaded_files, chat_history)
    
    async def _detect_intent(self, message: str, current_stage: int) -> str:
        """
        检测用户意图
        
        Returns:
            generate_report, stage_transition, general_chat
        """
        message_lower = message.lower()
        
        report_keywords = ["生成报告", "开始分析", "分析报告", "十年战略分析"]
        if any(kw in message_lower for kw in report_keywords):
            return "generate_report"
        
        transition_keywords = ["信息完整", "没有其他问题", "预判完整", "进入下一阶段", "确认完成", "没问题了"]
        if any(kw in message_lower for kw in transition_keywords):
            return "stage_transition"
        
        return "general_chat"
    
    async def _handle_report_generation(self, prediction: str, session_info: Dict, uploaded_files: List[Dict] = None) -> Dict[str, Any]:
        """
        处理报告生成
        """
        context = {
            "session_info": session_info,
            "chat_history": [],
            "uploaded_files": uploaded_files or []
        }
        report = await ten_year_agent.analyze(prediction, context)
        
        return {
            "type": "report",
            "content": report["content"],
            "sources": report["sources"],
            "stage": 4
        }
    
    async def _handle_stage_transition(self, current_stage: int) -> Dict[str, Any]:
        """
        处理阶段转换
        """
        next_stage = current_stage + 1
        
        stage_messages = {
            2: "好的，信息已确认。现在进入自由提问阶段，您有什么想了解或探讨的吗？",
            3: "好的，现在请告诉我您对选定赛道的十年预判：您认为十年后这个赛道会发展成什么样？市场规模、竞争格局、技术演进等方面都可以谈谈。",
            4: "好的，我将为您生成十年战略分析报告，请稍候..."
        }
        
        return {
            "type": "stage_transition",
            "content": stage_messages.get(next_stage, "进入下一阶段"),
            "stage": next_stage
        }
    
    async def _handle_general_chat(
        self,
        message: str,
        session_info: Dict,
        current_stage: int,
        uploaded_files: List[Dict] = None,
        chat_history: List[Dict] = None
    ) -> Dict[str, Any]:
        
        context = self._build_context(session_info, current_stage)
        
        history_text = ""
        if chat_history and len(chat_history) > 0:
            history_parts = []
            for msg in chat_history[-15:]:
                role_label = "用户" if msg["role"] == "user" else "顾问"
                content = msg.get("content", "")
                if content:
                    history_parts.append(f"**{role_label}**：{content}")
            if history_parts:
                history_text = "\n\n## 之前的对话记录（请参考这些内容来回复用户）\n\n" + "\n\n".join(history_parts)
        
        file_context = ""
        if uploaded_files:
            file_parts = []
            for f in uploaded_files:
                filename = f.get("filename", "未知文件")
                content = f.get("content", "")
                if content:
                    file_parts.append(f"\n### 文件：{filename}\n{content[:3000]}")
            if file_parts:
                file_context = "\n\n## 用户上传的文件内容\n" + "\n".join(file_parts)
        
        is_file_related = False
        if uploaded_files and ("文件" in message or "文档" in message or "上传" in message or "总结" in message or "分析" in message):
            is_file_related = True
        
        if uploaded_files and len(uploaded_files) > 0:
            is_file_related = True
        
        if is_file_related and uploaded_files:
            prompt = f"""你是一位资深的战略咨询顾问。用户上传了文件，请仔细阅读并深入分析文件内容。

## 用户背景
{context}
{history_text}

## 用户上传的文件内容
{file_context}

## 用户消息
{message}

请根据用户上传的文件内容和之前的对话记录，给出专业、有针对性的回复。

**重要要求：**
1. **核心内容总结**：首先用2-3段话总结文件的核心内容，包括：
   - 文件主题和目的
   - 关键信息和数据
   - 主要结论或观点

2. **关联性分析**：分析文件内容与用户企业背景、战略方向的关系：
   - 文件信息如何支持或影响战略决策
   - 与选定赛道的关联性
   - 与愿景使命的一致性

3. **价值提炼**：提炼文件中对战略决策有价值的信息：
   - 优势资源或能力
   - 潜在机会或风险
   - 关键行动建议

4. **回复要求**：
   - 必须基于文件实际内容进行分析，不要编造信息
   - 引用文件中的具体数据或观点
   - 回复结构清晰，重点突出
   - 语言简洁有力"""
        else:
            prompt = f"""你是一位资深的战略咨询顾问，正在与用户进行深度对话。

## 用户背景
{context}
{history_text}

## 当前阶段
第{current_stage}阶段（共4阶段）：
- 阶段1：信息补充
- 阶段2：自由提问探讨
- 阶段3：预判采集
- 阶段4：报告生成

## 用户消息
{message}

请根据用户消息、之前的对话记录和当前阶段，给出专业、有针对性的回复。

要求：
1. 回复要紧密结合用户的企业背景和赛道特点
2. 如果用户在提问，给出专业且有深度的回答
3. 如果用户在补充信息，确认并整理信息
4. 适当引导用户进入下一阶段，但不要强制
5. 回复简洁有力，不要过于冗长"""
        
        response = await llm_service.generate(prompt, temperature=0.6)
        
        return {
            "type": "chat",
            "content": response,
            "stage": current_stage
        }
    
    def _build_context(self, session_info: Dict, current_stage: int) -> str:
        """构建对话上下文"""
        parts = []
        
        if session_info.get("company_name"):
            parts.append(f"企业名称：{session_info['company_name']}")
        if session_info.get("industry"):
            parts.append(f"所属行业：{session_info['industry']}")
        if session_info.get("stage"):
            parts.append(f"企业阶段：{session_info['stage']}")
        if session_info.get("selected_track"):
            parts.append(f"选定赛道：{session_info['selected_track']}")
        if session_info.get("vision"):
            parts.append(f"愿景：{session_info['vision']}")
        if session_info.get("mission"):
            parts.append(f"使命：{session_info['mission']}")
        if session_info.get("values"):
            parts.append(f"价值观：{', '.join(session_info['values'])}")
        
        return "\n".join(parts) if parts else "暂无背景信息"

orchestrator_agent = OrchestratorAgent()
