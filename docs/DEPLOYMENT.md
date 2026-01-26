# 部署与运行

## 本地运行（开发）
- Python 3.10+
- 建议使用虚拟环境

安装依赖：

```bash
pip install -r requirements.txt
```

准备配置：
- 复制 .env.example 为 .env，并补全 SILICON_FLOW_* 与 DB_* 配置

启动后端（同时挂载前端静态文件）：

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 9001 --reload
```

访问：
- 页面：http://127.0.0.1:9001/
- API：http://127.0.0.1:9001/api/courses
- AI（流式）：http://127.0.0.1:9001/api/ai/chat

## 线上部署（简述）
线上以 systemd 方式运行 FastAPI（uvicorn），由 Nginx 反向代理与 TLS 终止。

详细配置见：
- docs/SERVER.md
