# VMV-SOP战略咨询系统

基于"From VMV to SOP"理论的AI驱动战略咨询系统，帮助创业者和企业管理者进行深度战略分析。

## 功能特性

- ✅ **初始化信息采集**：采集VMV（愿景、使命、价值观）和企业基本信息
- ✅ **多轮对话交互**：支持自然语言对话，上下文记忆
- ✅ **文件上传解析**：支持PDF、Word文档解析
- ✅ **十年战略分析**：基于用户预判生成正反论据和综合判断
- ✅ **搜索API集成**：实时获取行业数据和趋势
- ✅ **报告导出**：支持Markdown、PDF、Word格式导出
- ✅ **玻璃拟态UI**：现代化的视觉体验

## 技术栈

### 后端
- FastAPI - 高性能异步Web框架
- SQLAlchemy - ORM
- 智谱GLM-4 + 千问Max - 大模型双备份
- Serper/Tavily - 搜索API
- PyMuPDF + python-docx - 文件解析

### 前端
- React 18 + TypeScript
- Vite - 构建工具
- Ant Design - UI组件库
- Zustand - 状态管理

## 快速开始

### 环境要求

- Python 3.10+
- Node.js 18+

### 安装步骤

1. **运行安装脚本**
   ```bash
   install.bat
   ```

2. **配置API密钥**
   
   编辑 `backend/.env` 文件，填入您的API密钥：
   ```env
   ZHIPU_API_KEY=your_zhipu_api_key
   QWEN_API_KEY=your_qwen_api_key
   SERPER_API_KEY=your_serper_api_key
   ```

3. **启动服务**
   ```bash
   start.bat
   ```

### 手动启动

**后端：**
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --port 8000
```

**前端：**
```bash
cd frontend
npm install
npm run dev
```

## 项目结构

```
vmv-sop-strategy-ai-V5/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── api/            # API路由
│   │   ├── agents/         # Agent模块
│   │   ├── services/       # 服务层
│   │   ├── models/         # 数据模型
│   │   └── main.py         # 应用入口
│   ├── requirements.txt
│   └── .env.example
├── frontend/                # 前端代码
│   ├── src/
│   │   ├── pages/          # 页面组件
│   │   ├── services/       # API服务
│   │   ├── stores/         # 状态管理
│   │   └── styles/         # 样式文件
│   ├── package.json
│   └── vite.config.ts
├── docs/                    # 文档
│   ├── PRD_战略咨询系统.md
│   ├── 技术开发路线.md
│   └── 架构设计.md
├── install.bat              # 安装脚本
├── start.bat                # 启动脚本
└── README.md
```

## API文档

启动后端服务后，访问 http://localhost:8000/docs 查看Swagger API文档。

### 主要接口

| 接口 | 方法 | 描述 |
|------|------|------|
| `/api/sessions` | POST | 创建会话 |
| `/api/sessions/{id}` | GET | 获取会话详情 |
| `/api/chat/send` | POST | 发送消息 |
| `/api/chat/history/{id}` | GET | 获取对话历史 |
| `/api/chat/upload` | POST | 上传文件 |
| `/api/report/generate` | POST | 生成报告 |
| `/api/report/{id}/export` | GET | 导出报告 |

## 使用流程

1. **初始化**：填写企业VMV信息和基本情况
2. **信息补充**：确认或补充企业信息
3. **自由提问**：就战略问题进行探讨
4. **预判采集**：输入对选定赛道的十年预判
5. **报告生成**：系统生成分析报告

## 配置说明

### 大模型配置

系统支持智谱GLM-4和千问Max双备份，当一个模型调用失败时自动切换。

### 搜索API配置

支持Serper和Tavily两种搜索服务，用于获取实时行业数据。

## 扩展性

系统预留了五年、三年、一年战略Agent接口，可根据需要扩展。

## 许可证

MIT License
