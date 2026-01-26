# 服务器信息（线上环境）

## 基本信息
- 域名：schedule.oyemoye.top
- 内网反代目标：127.0.0.1:9001
- 项目目录：/opt/schedule-app
- 后端目录：/opt/schedule-app/backend
- 运行用户：root

## systemd
- 服务名：schedule-app.service
- 单元文件：/etc/systemd/system/schedule-app.service
- 工作目录：/opt/schedule-app
- 启动命令：/opt/schedule-app/backend/venv/bin/uvicorn backend.main:app --host 127.0.0.1 --port 9001 --log-level debug

常用命令：
- 查看状态：systemctl status schedule-app.service
- 重启服务：systemctl restart schedule-app.service
- 查看日志：journalctl -u schedule-app.service -n 200 --no-pager

## Nginx
- 配置文件：/etc/nginx/sites-available/schedule-app
- 启用链接：/etc/nginx/sites-enabled/schedule-app
- 证书：由 Certbot 管理（/etc/letsencrypt/live/schedule.oyemoye.top）

## 环境变量与密钥
- 线上环境变量文件：/opt/schedule-app/.env
- 说明：该文件包含数据库与模型 API Key 等敏感信息，禁止提交到 Git；本仓库仅保留 .env.example 作为模板。

## 代码更新方式（推荐流程）
- 拉取代码：在 /opt/schedule-app 执行 git pull（如服务器已配置仓库与凭据）
- 或手工同步：将改动文件 scp 到 /opt/schedule-app/backend/ 或 /opt/schedule-app/frontend/
- 重启服务：systemctl restart schedule-app.service

## 健康检查
- 本机：curl -s http://127.0.0.1:9001/ | head
- 线上：访问 https://schedule.oyemoye.top/
- AI 接口（流式）：POST https://schedule.oyemoye.top/api/ai/chat（返回 NDJSON，每行一个 JSON）
