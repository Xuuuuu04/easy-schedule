# 课程表排课助手

一个用于管理学生与课程安排的轻量 Web 应用：后端 FastAPI + 前端静态页面，并提供 AI 助手（支持工具调用与流式输出）。

## 功能
- 课程管理：新增/修改/删除/查询课程
- 学生管理：新增/修改/删除/查询学生
- AI 助手：通过 /api/ai/chat 进行流式对话，并可调用后端工具查询/生成信息

## 目录结构
- backend/：FastAPI 后端与 AI Agent（LangGraph/LangChain）
- frontend/：静态前端（由后端挂载到 /）
- docs/：部署与服务器信息
- .env.example：环境变量模板（不包含任何密钥）

## 本地启动
1) 安装依赖

```bash
pip install -r requirements.txt
```

2) 配置环境变量
- 复制 .env.example 为 .env
- 填写模型与数据库相关配置

3) 启动服务

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 9001 --reload
```

4) 访问
- 页面：http://127.0.0.1:9001/
- AI（流式）：POST http://127.0.0.1:9001/api/ai/chat

## AI 接口说明（流式）
- 路径：POST /api/ai/chat
- 请求体：

```json
{ "message": "你好", "thread_id": "default" }
```

- 返回：NDJSON（每行一个 JSON），常见类型：
  - {"type":"token","content":"..."}
  - {"type":"thinking","content":"..."}（若模型提供推理片段）
  - {"type":"tool_start","name":"..."} / {"type":"tool_end","name":"..."}

## 部署
- 本地与线上简要说明：docs/DEPLOYMENT.md
- 线上服务器关键信息与维护入口：docs/SERVER.md


## 开发进度（截至 2026-02-07）
- 已完成可公开仓库基线整理：补齐许可证、清理敏感与内部说明文件。
- 当前版本可构建/可运行，后续迭代以 issue 与提交记录持续公开追踪。
