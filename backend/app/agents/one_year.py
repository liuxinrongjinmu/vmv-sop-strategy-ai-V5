from typing import Dict, Any, List
import re
import time
import logging
from app.agents.base import BaseAgent
from app.services.llm import llm_service
from app.prompts.one_year import get_one_year_prompt

logger = logging.getLogger(__name__)


class OneYearAgent(BaseAgent):
    """
    一年战略Agent
    聚焦"任务分解"与"战略屋"

    将三年目标分解为年度任务，用战略屋拆解为关键战场/战役/战斗，
    明确胜利标准，验证逻辑链，完成组织战与财务验算，
    初步设立各部门各岗位关键工作流程SOP。
    """

    name = "one_year_strategy"
    report_title = "一年战略任务分解与战略屋报告"

    async def analyze(
        self,
        prediction: str,
        context: Dict[str, Any],
        ten_year_report: str = "",
        five_year_report: str = "",
        three_year_report: str = "",
    ) -> Dict[str, Any]:
        """
        执行一年战略分析

        :param prediction: 用户的预判内容
        :param context: 包含session_info, chat_history, uploaded_files
        :param ten_year_report: 十年战略报告内容（如果有）
        :param five_year_report: 五年战略报告内容（如果有）
        :param three_year_report: 三年战略报告内容（如果有）
        :return: {"title": "...", "content": "...", "sources": [...]}
        """
        session_info = context.get("session_info", {})
        chat_history = context.get("chat_history", [])
        uploaded_files = context.get("uploaded_files", [])

        logger.info(f"一年战略分析开始... 预测: {prediction[:80]}...")

        # 构建上下文信息
        context_text = self._build_context(session_info, chat_history, uploaded_files)

        # 搜索外部数据支撑（自定义搜索查询——聚焦年度规划、人才市场、成本结构）
        search_queries = []
        track = session_info.get("selected_track", "")
        industry = session_info.get("industry", "")
        if track:
            search_queries.append(f"{track} 年度战略规划 执行计划 案例")
        if industry and industry != track:
            search_queries.append(f"{industry} 企业 年度目标 分解执行")
        search_queries.append(f"{track or industry} 人才市场 薪酬水平 招聘趋势")
        search_queries.append(f"{track or industry} 成本结构 运营成本 盈亏平衡")
        search_results, search_context = await self._search_evidence(
            prediction, session_info, search_queries=search_queries
        )

        # 带降级的报告生成
        result = await self._generate_with_fallback(
            prediction, context_text, search_context,
            lambda p, c, s: self._generate_report_single_call(p, c, s, ten_year_report, five_year_report, three_year_report),
            lambda p, c, s: self._generate_simplified_report(p, c, s, ten_year_report, five_year_report, three_year_report),
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
        three_year_report: str = "",
    ) -> str:
        """单次LLM调用生成完整一年战略报告（深度版）"""

        search_section = ""
        if search_context:
            search_section = f"""
{search_context}

**重要：** 请在任务分解、组织战和财务验算中，积极引用上述搜索到的外部数据来支撑你的论证。引用时标注"据外部数据"或"根据行业报告"。
"""

        ten_year_section = ""
        if ten_year_report:
            ten_year_section = f"""
## 十年战略预判报告（已生成）
{ten_year_report[:1500]}
"""

        five_year_section = ""
        if five_year_report:
            five_year_section = f"""
## 五年战略关键驱动因素报告（已生成）
{five_year_report[:1500]}
"""

        three_year_section = ""
        if three_year_report:
            three_year_section = f"""
## 三年战略阶段性目标报告（已生成）
{three_year_report[:1500]}
"""

        strategy_base_section = ""
        if ten_year_section or five_year_section or three_year_section:
            strategy_base_section = f"""
{ten_year_section}
{five_year_section}
{three_year_section}

**重要：** 一年任务分解必须严格基于上述三年目标，战略屋的每个战场/战役/战斗都要能追溯到三年目标。逻辑链验证是核心——战斗胜利→战役胜利→战场胜利→总目标达成，任何环节断裂都需要重新设计。
"""

        prompt = get_one_year_prompt(prediction, context_text, strategy_base_section, search_section)

        response = await llm_service.generate(
            prompt, temperature=0.35, max_tokens=7000
        )

        # 清理响应内容
        content = response.strip()

        # 确保以标题开头
        if not content.startswith("#"):
            content = "# 一年战略任务分解与战略屋报告\n\n" + content

        return content

    async def _generate_simplified_report(
        self,
        prediction: str,
        context_text: str,
        search_context: str = "",
        ten_year_report: str = "",
        five_year_report: str = "",
        three_year_report: str = "",
    ) -> str:
        """备用方案：生成简化版一年战略报告"""

        search_hint = ""
        if search_context:
            search_hint = (
                "\n\n请参考以下外部数据支撑你的分析：\n" + search_context[:1500]
            )

        ten_year_hint = ""
        if ten_year_report:
            ten_year_hint = (
                "\n\n十年战略报告核心结论：\n" + ten_year_report[:600]
            )

        five_year_hint = ""
        if five_year_report:
            five_year_hint = (
                "\n\n五年战略关键驱动因素：\n" + five_year_report[:600]
            )

        three_year_hint = ""
        if three_year_report:
            three_year_hint = (
                "\n\n三年战略目标核心要点：\n" + three_year_report[:800]
            )

        prompt = f"""基于以下信息生成简化的一年战略任务分解与战略屋报告（Markdown格式）：

{context_text}
{search_hint}
{ten_year_hint}
{five_year_hint}
{three_year_hint}

用户预判：{prediction}

请包含：年度任务摘要、战略基础回顾、2-3项年度核心任务、战略屋（2-3个战场，每战场1-2个战役，每战役1-2个战斗）、逻辑验证、组织战概要、财务验算概要、SOP清单、执行时间表。
每个部分精简到150字以内。直接输出报告内容。"""

        response = await llm_service.generate(
            prompt, temperature=0.5, max_tokens=3000
        )
        return response.strip()

    def _get_default_report(self, prediction: str) -> str:
        """返回默认报告（兜底方案）"""
        return f"""# 一年战略任务分解与战略屋报告

## 一、年度任务摘要
基于三年目标分解，本年度聚焦产品开发、市场拓展、组织建设三大任务，通过4个关键战场、8个核心战役、16个关键战斗的层层分解，确保年度总目标达成。

---

## 二、战略基础回顾

### 2.1 十年预判核心方向
{prediction[:150]}

### 2.2 五年关键驱动因素
- 技术创新加速（近距/高借势）
- 消费习惯演变（近距/高借势）

### 2.3 三年目标核心要点
- 市场地位目标：建立显著市场地位
- 产品技术目标：建立核心技术能力
- 组织能力目标：建立匹配的人才体系

---

## 三、年度任务分解

### 3.1 完成核心产品开发与上线
**承接三年目标：** 产品技术目标
**完成标准：** 核心产品上线并获得首批用户验证
**优先级：** P0 | **预估周期：** Q1-Q2

### 3.2 建立市场拓展体系
**承接三年目标：** 市场地位目标
**完成标准：** 获取首批XX个付费客户
**优先级：** P0 | **预估周期：** Q2-Q4

### 3.3 搭建核心团队
**承接三年目标：** 组织能力目标
**完成标准：** 核心岗位到位率90%
**优先级：** P0 | **预估周期：** Q1-Q3

---

## 四、战略屋

### 4.1 战略屋总览

```
                    ┌─────────────────────┐
                    │   年度总目标         │
                    │ 产品上线+市场验证    │
                    └──────────┬──────────┘
               ┌───────────────┼───────────────┐
               ▼               ▼               ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │产品战场   │   │市场战场   │   │组织战场   │
        └────┬─────┘   └────┬─────┘   └────┬─────┘
             │              │              │
         ┌───┴───┐      ┌───┴───┐      ┌───┴───┐
         ▼       ▼      ▼       ▼      ▼       ▼
       战役1.1 战役1.2 战役2.1 战役2.2 战役3.1 战役3.2
```

### 4.2 战场一：产品战场

**战役1.1 核心产品开发**
| 战斗 | 胜利标准 | 完成时间 | 可实现性 |
|------|---------|---------|---------|
| 1.1.1 MVP开发 | 核心功能可用 | Q1 | 高 |
| 1.1.2 产品测试 | 用户测试通过 | Q2 | 高 |

**战役1.2 产品迭代优化**
| 战斗 | 胜利标准 | 完成时间 | 可实现性 |
|------|---------|---------|---------|
| 1.2.1 V1.1发布 | 核心反馈修复 | Q3 | 高 |
| 1.2.2 V2.0规划 | 规划方案确定 | Q4 | 中 |

### 4.3 战场二：市场战场

**战役2.1 市场验证**
| 战斗 | 胜利标准 | 完成时间 | 可实现性 |
|------|---------|---------|---------|
| 2.1.1 种子用户获取 | 50+种子用户 | Q2 | 中 |
| 2.1.2 付费转化验证 | 首批付费用户 | Q3 | 中 |

**战役2.2 市场拓展**
| 战斗 | 胜利标准 | 完成时间 | 可实现性 |
|------|---------|---------|---------|
| 2.2.1 渠道建设 | 2+有效渠道 | Q3 | 中 |
| 2.2.2 规模化获客 | 月增长20% | Q4 | 低 |

### 4.4 战场三：组织战场

**战役3.1 核心团队组建**
| 战斗 | 胜利标准 | 完成时间 | 可实现性 |
|------|---------|---------|---------|
| 3.1.1 技术团队 | 技术团队到位 | Q1 | 高 |
| 3.1.2 市场团队 | 市场负责人到岗 | Q2 | 中 |

**战役3.2 组织机制建设**
| 战斗 | 胜利标准 | 完成时间 | 可实现性 |
|------|---------|---------|---------|
| 3.2.1 绩效体系 | 绩效方案落地 | Q3 | 中 |
| 3.2.2 协作流程 | 核心SOP建立 | Q4 | 高 |

---

## 五、逻辑验证

逻辑链验证：战斗胜利→战役胜利→战场胜利→总目标达成
- 产品战场胜利 → 核心产品上线可用 ✓
- 市场战场胜利 → 获得市场验证和付费用户 ✓
- 组织战场胜利 → 团队到位支撑业务 ✓
- 三战场协同 → 年度总目标达成 ✓

薄弱环节：市场拓展的可实现性较低，需要重点关注。

---

## 六、组织战

### 核心岗位需求
| 岗位 | 人数 | 到岗时间 | 优先级 |
|------|------|---------|--------|
| 技术负责人 | 1人 | Q1 | P0 |
| 产品经理 | 1人 | Q1 | P0 |
| 市场负责人 | 1人 | Q2 | P1 |
| 销售经理 | 1-2人 | Q3 | P1 |

---

## 七、财务验算

### 收入预测
| 项目 | Q1 | Q2 | Q3 | Q4 | 全年 |
|------|----|----|----|----|------|
| 主营收入 | 0 | 少量 | 中等 | 增长 | 根据实际 |

### 成本预算
| 成本项 | 占比 |
|--------|------|
| 人力成本 | 50% |
| 研发投入 | 25% |
| 市场费用 | 15% |
| 运营成本 | 10% |

### 盈亏平衡
预计Q3-Q4达到月度盈亏平衡，前提是产品按时上线且市场拓展顺利。

---

## 八、SOP初步框架

| 优先级 | SOP名称 | 对应战斗 | 建立时间 |
|--------|---------|---------|---------|
| P0 | 产品开发流程 | 1.1.1 | Q1 |
| P0 | 用户反馈处理流程 | 1.2.1 | Q3 |
| P1 | 客户获取流程 | 2.1.1 | Q2 |
| P1 | 招聘面试流程 | 3.1.1 | Q1 |
| P2 | 绩效考核流程 | 3.2.1 | Q3 |

---

## 九、执行时间表

| 季度 | 关键节点 | 交付物 |
|------|---------|--------|
| Q1 | 核心团队组建+MVP开发 | 团队到位+产品原型 |
| Q2 | 产品上线+种子用户 | 产品上线+首批用户 |
| Q3 | 产品迭代+市场验证 | V1.1+付费用户 |
| Q4 | 规模化拓展+年度复盘 | 增长数据+年度总结 |"""


one_year_agent = OneYearAgent()
