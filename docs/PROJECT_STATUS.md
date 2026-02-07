# EasySchedule（课程表排课助手）- 项目体检

最后复核：2026-02-05

## 状态
- 状态标签：active
- 定位：轻量课程/学生管理 Web 应用 + AI 流式助手（可工具调用）。

## 架构速览
- 单体 FastAPI：`backend/main.py`
  - 业务 CRUD：`backend/service.py` + `backend/models.py`
  - AI：`backend/ai_service.py` + `backend/ai_graph.py` + `backend/tools.py`
  - 前端：静态资源挂载 `frontend/` 到 `/`
- 文档：
  - 部署与运行：`docs/DEPLOYMENT.md`
  - 线上维护：`docs/SERVER.md`

## 运行
- 本地：`python -m uvicorn backend.main:app --port 9001 --reload`
- 配置：`.env.example` → `.env`

## 风险与建议（优先级）
- 建议把 AI 流式接口的 `media_type` 改为 `application/x-ndjson`（当前标注为 `application/json`，但语义是逐行 NDJSON）。
- 若后续要做作品集强化：补最小“坏例库 + 回归脚本”，避免模型/提示变更导致对话质量回退不可控。

