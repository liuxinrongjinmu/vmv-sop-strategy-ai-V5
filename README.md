# VMV-SOP 战略咨询系统

基于 **"From VMV to SOP"** 理论的 AI 驱动战略咨询系统，帮助创业者和企业管理者进行深度战略分析。

---

## 📖 目录

- [项目概述](#项目概述)
- [需求说明](#需求说明)
- [技术实现方案](#技术实现方案)
- [架构流程设计](#架构流程设计)
- [功能特性](#功能特性)
- [技术栈](#技术栈)
- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [API文档](#api文档)
- [部署指南](#部署指南)
- [使用流程](#使用流程)

---

## 项目概述

### 背景

"From VMV to SOP" 是一个企业系统工程理论，旨在帮助企业从创始人的初心（VMV）出发，通过系统化的战略规划，最终固化为可执行的标准化运营流程（SOP）。

### 核心价值

本系统将这一理论转化为实际的 AI 驱动应用，提供：

- **VMV 梳理**：帮助企业明确愿景、使命、价值观
- **战略分析**：基于十年预判的深度赛道分析
- **智能对话**：多轮对话交互，深入理解企业需求
- **报告生成**：专业的战略分析报告，支持多格式导出

---

## 需求说明

### 核心需求

1. **初始化信息采集**
   - 企业基本信息（名称、行业、规模、阶段）
   - VMV 信息（愿景、使命、价值观）
   - 选定赛道

2. **多轮对话交互**
   - 信息补充与确认
   - 自由提问探讨
   - 预判采集

3. **十年战略分析**
   - 正面论据分析
   - 反面论据分析
   - 综合判断

4. **报告生成与导出**
   - Markdown 格式
   - PDF 格式
   - Word 格式

5. **文件上传解析**
   - 支持 PDF 文档
   - 支持 Word 文档
   - 文件内容融入分析

---

## 技术实现方案

### 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                        前端 (React + Vite)                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │  初始化页面  │  │  聊天页面   │  │  报告导出           │  │
│  │  InitPage   │  │  ChatPage   │  │  (MD/PDF/DOCX)     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP/HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                     后端 (FastAPI + Python)                   │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                    API Layer                         │    │
│  │  /api/sessions  /api/chat  /api/report              │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                   Agent Layer                        │    │
│  │  OrchestratorAgent  →  TenYearAgent                 │    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                  Service Layer                       │    │
│  │  LLMService  SearchService  FileParser  ReportExport│    │
│  └─────────────────────────────────────────────────────┘    │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                   Data Layer                         │    │
│  │  SQLAlchemy  →  SQLite (Async)                      │    │
│  └─────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                     外部服务                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ 智谱 GLM-4   │  │ 千问 Max     │  │ Tavily Search│       │
│  │ (主LLM)      │  │ (备用LLM)    │  │ (搜索API)    │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### 核心模块设计

#### 1. Agent 层

**OrchestratorAgent（总控 Agent）**
- 负责调度和协调其他 Agent
- 检测用户意图（报告生成、阶段转换、普通对话）
- 维护会话状态和上下文

**TenYearAgent（十年战略 Agent）**
- 执行赛道预判分析
- 提取关键洞察
- 搜索支撑证据
- 构建正反论据
- 生成综合判断

#### 2. Service 层

**LLMService**
- 支持智谱 GLM-4 和千问 Max 双备份
- 自动故障切换机制

**SearchService**
- 集成 Tavily 搜索 API
- 获取实时行业数据和趋势

**FileParser**
- 支持 PDF 解析（PyMuPDF）
- 支持 Word 解析（python-docx）

**ReportExport**
- Markdown 生成
- PDF 生成（ReportLab）
- Word 生成（python-docx）

---

## 架构流程设计

### 用户交互流程

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  初始化页面  │────▶│  聊天页面   │────▶│  报告生成   │
│  (Stage 1)  │     │  (Stage 2-3)│     │  (Stage 4)  │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       ▼                   ▼                   ▼
  填写 VMV           多轮对话交流         生成分析报告
  企业信息           上传文件解析         导出多格式
  选定赛道           预判采集
```

### 报告生成流程

```
用户预判输入
     │
     ▼
┌─────────────────┐
│ 提取关键洞察     │◀── 聊天历史 + 上传文件
└────────┬────────┘
         ▼
┌─────────────────┐
│ 企业深度分析     │◀── VMV + 企业背景
└────────┬────────┘
         ▼
┌─────────────────┐
│ 提取核心假设     │◀── 预判内容
└────────┬────────┘
         ▼
┌─────────────────┐
│ 搜索支撑证据     │◀── Tavily API
└────────┬────────┘
         ▼
┌─────────────────┐
│ 构建正反论据     │◀── LLM 分析
└────────┬────────┘
         ▼
┌─────────────────┐
│ 生成综合判断     │
└────────┬────────┘
         ▼
   输出分析报告
```

---

## 功能特性

### ✅ 初始化信息采集
- 企业基本信息录入（名称、行业、规模、阶段）
- VMV 信息采集（愿景、使命、价值观）
- 选定赛道输入
- 数据本地缓存，支持断点续填

### ✅ 多轮对话交互
- 自然语言对话，上下文记忆
- 智能意图识别
- 阶段自动流转
- 文件上传与解析

### ✅ 文件上传解析
- 支持 PDF 文档上传
- 支持 Word 文档上传
- 文件内容自动融入对话和分析

### ✅ 十年战略分析
- 基于用户预判的深度分析
- 正面论据：市场机会、竞争优势、成功案例
- 反面论据：市场风险、竞争威胁、失败案例
- 综合判断：SWOT 分析、情景分析、关键假设

### ✅ 搜索 API 集成
- Tavily 搜索 API
- 实时获取行业数据和趋势
- 支撑论据的可信度验证

### ✅ 报告导出
- Markdown 格式导出
- PDF 格式导出（专业排版）
- Word 格式导出（可编辑）

### ✅ 玻璃拟态 UI
- 现代化视觉体验
- 响应式设计
- 流畅动画效果

---

## 技术栈

### 后端

| 技术 | 版本 | 说明 |
|------|------|------|
| Python | 3.10+ | 编程语言 |
| FastAPI | 0.104.0+ | 高性能异步 Web 框架 |
| SQLAlchemy | 2.0.0+ | ORM 框架 |
| aiosqlite | 0.19.0+ | 异步 SQLite |
| Pydantic | 2.5.0+ | 数据验证 |
| httpx | 0.25.0+ | 异步 HTTP 客户端 |
| PyMuPDF | 1.23.0+ | PDF 解析 |
| python-docx | 1.1.0+ | Word 文档处理 |
| ReportLab | 4.0.0+ | PDF 生成 |
| uvicorn | 0.24.0+ | ASGI 服务器 |

### 前端

| 技术 | 版本 | 说明 |
|------|------|------|
| React | 18.2.0+ | UI 框架 |
| TypeScript | 5.3.0+ | 类型安全 |
| Vite | 5.0.0+ | 构建工具 |
| React Router | 6.20.0+ | 路由管理 |
| Axios | 1.6.0+ | HTTP 客户端 |
| Zustand | 4.4.0+ | 状态管理 |
| Ant Design | 5.12.0+ | UI 组件库 |
| react-markdown | 9.0.0+ | Markdown 渲染 |

### 外部服务

| 服务 | 说明 |
|------|------|
| 智谱 GLM-4 | 主 LLM 服务 |
| 千问 Max | 备用 LLM 服务 |
| Tavily | 搜索 API |

---

## 项目结构

```
vmv-sop-strategy-ai-V5/
├── backend/                      # 后端代码
│   ├── app/
│   │   ├── agents/               # Agent 模块
│   │   │   ├── __init__.py
│   │   │   ├── orchestrator.py   # 总控 Agent
│   │   │   └── ten_year.py       # 十年战略 Agent
│   │   ├── api/                  # API 路由
│   │   │   ├── __init__.py
│   │   │   ├── sessions.py       # 会话管理
│   │   │   ├── chat.py           # 聊天接口
│   │   │   └── report.py         # 报告接口
│   │   ├── core/                 # 核心模块
│   │   │   ├── __init__.py
│   │   │   └── database.py       # 数据库配置
│   │   ├── models/               # 数据模型
│   │   │   ├── __init__.py
│   │   │   └── models.py         # ORM 模型
│   │   ├── schemas/              # 数据模式
│   │   │   ├── __init__.py
│   │   │   └── schemas.py        # Pydantic 模型
│   │   ├── services/             # 服务层
│   │   │   ├── __init__.py
│   │   │   ├── llm.py            # LLM 服务
│   │   │   ├── search.py         # 搜索服务
│   │   │   ├── file_parser.py    # 文件解析
│   │   │   └── report_export.py  # 报告导出
│   │   ├── __init__.py
│   │   ├── config.py             # 配置管理
│   │   └── main.py               # 应用入口
│   ├── .env.example              # 环境变量示例
│   ├── Dockerfile                # Docker 配置
│   ├── docker-compose.yml        # Docker Compose
│   └── requirements.txt          # Python 依赖
│
├── frontend/                     # 前端代码
│   ├── src/
│   │   ├── pages/                # 页面组件
│   │   │   ├── InitPage.tsx      # 初始化页面
│   │   │   ├── InitPage.css
│   │   │   ├── ChatPage.tsx      # 聊天页面
│   │   │   └── ChatPage.css
│   │   ├── services/             # API 服务
│   │   │   ├── api.ts            # Axios 配置
│   │   │   ├── session.ts        # 会话服务
│   │   │   ├── chat.ts           # 聊天服务
│   │   │   └── report.ts         # 报告服务
│   │   ├── stores/               # 状态管理
│   │   │   └── appStore.ts       # 全局状态
│   │   ├── styles/               # 样式文件
│   │   │   └── glassmorphism.css # 玻璃拟态样式
│   │   ├── types/                # 类型定义
│   │   │   ├── session.ts
│   │   │   ├── message.ts
│   │   │   └── report.ts
│   │   ├── App.tsx               # 根组件
│   │   ├── main.tsx              # 入口文件
│   │   └── vite-env.d.ts         # Vite 类型
│   ├── .env.example              # 环境变量示例
│   ├── index.html                # HTML 模板
│   ├── package.json              # NPM 配置
│   ├── tsconfig.json             # TypeScript 配置
│   └── vite.config.ts            # Vite 配置
│
├── .gitignore                    # Git 忽略配置
├── README.md                     # 项目说明
├── install.bat                   # 安装脚本
├── start.bat                     # 启动脚本
├── vercel.json                   # Vercel 配置
└── zeabur.yaml                   # Zeabur 配置
```

---

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+

### 安装步骤

#### 方式一：使用脚本（Windows）

```bash
# 1. 运行安装脚本
install.bat

# 2. 配置环境变量
# 编辑 backend/.env 文件，填入您的 API 密钥

# 3. 启动服务
start.bat
```

#### 方式二：手动安装

**后端：**

```bash
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入 API 密钥

# 启动服务
python -m uvicorn app.main:app --reload --port 8000
```

**前端：**

```bash
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置后端地址

# 启动开发服务器
npm run dev
```

### 环境变量配置

**后端 (backend/.env)：**

```env
ZHIPU_API_KEY=your_zhipu_api_key
QWEN_API_KEY=your_qwen_api_key
TAVILY_API_KEY=your_tavily_api_key
```

**前端 (frontend/.env)：**

```env
VITE_API_URL=http://localhost:8000
```

---

## API文档

启动后端服务后，访问 http://localhost:8000/docs 查看 Swagger API 文档。

### 主要接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/sessions` | POST | 创建会话 |
| `/api/sessions/{id}` | GET | 获取会话详情 |
| `/api/chat/send` | POST | 发送消息 |
| `/api/chat/upload` | POST | 上传文件 |
| `/api/report/generate` | POST | 生成报告 |
| `/api/report/{id}/export` | GET | 导出报告 |

### 创建会话

```http
POST /api/sessions
Content-Type: application/json

{
  "vision": "成为行业领导者",
  "mission": "为客户提供优质服务",
  "values": ["创新", "诚信", "卓越"],
  "company_name": "示例公司",
  "industry": "科技",
  "stage": "0-1",
  "team_size": "1-10",
  "selected_track": "人工智能",
  "additional_info": "补充信息"
}
```

### 发送消息

```http
POST /api/chat/send
Content-Type: application/json

{
  "session_id": "session_uuid",
  "content": "用户消息内容"
}
```

### 生成报告

```http
POST /api/report/generate
Content-Type: application/json

{
  "session_id": "session_uuid",
  "prediction": "我对这个赛道的十年预判..."
}
```

---

## 部署指南

### 部署架构

```
前端 → EdgeOne / Vercel / Zeabur（静态网站托管）
后端 → Railway / Zeabur（API 服务托管）
```

### 后端部署（Railway）

1. 访问 https://railway.app
2. 使用 GitHub 登录
3. 创建新项目，选择仓库
4. 配置 Root Directory 为 `backend`
5. 添加环境变量（API 密钥）
6. 部署并获取 URL

### 前端部署（EdgeOne/Vercel/Zeabur）

1. 连接 GitHub 仓库
2. 配置构建命令：`cd frontend && npm install && npm run build`
3. 配置输出目录：`frontend/dist`
4. 添加环境变量：`VITE_API_URL=后端URL`
5. 部署并获取 URL

### 注意事项

- 确保后端 CORS 配置正确
- 前端环境变量 `VITE_API_URL` 不要加 `/api` 后缀
- API 密钥不要提交到代码仓库

---

## 使用流程

### 1. 初始化阶段
- 填写企业基本信息
- 输入 VMV（愿景、使命、价值观）
- 选择细分赛道
- 点击"完成初始化，进入对话"

### 2. 信息补充阶段
- 系统确认企业信息
- 用户补充或修改信息
- 上传相关文件（可选）

### 3. 自由提问阶段
- 与 AI 进行深度对话
- 探讨战略相关问题
- 上传文件获取分析

### 4. 预判采集阶段
- 输入对选定赛道的十年预判
- 描述市场趋势、竞争格局等

### 5. 报告生成阶段
- 系统自动生成分析报告
- 包含正反论据和综合判断
- 支持导出 MD/PDF/Word 格式

---

## 许可证

MIT License

---

## 联系方式

如有问题或建议，请提交 Issue 或 Pull Request。