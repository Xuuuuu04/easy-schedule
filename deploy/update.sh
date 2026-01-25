#!/bin/bash

# 部署脚本 - 用于服务器端更新代码并重启服务

# 1. 更新代码
echo "正在拉取最新代码..."
git reset --hard
git pull

# 2. 安装依赖
echo "正在检查依赖..."
pip install -r requirements.txt

# 3. 提示数据库操作
echo "----------------------------------------------------------------"
echo "如果这是首次部署或数据库凭证已更改，请确保数据库已初始化。"
echo "可以使用以下命令初始化数据库用户（需要 root 密码）："
echo "sudo mysql < deploy/init_db.sql"
echo "----------------------------------------------------------------"

# 4. 重启服务
echo "正在重启服务..."
# 停止旧进程
pkill -f "uvicorn backend.main:app" || true

# 等待端口释放
sleep 2

# 启动新进程 (后台运行)
nohup uvicorn backend.main:app --host 0.0.0.0 --port 8000 > app.log 2>&1 &

echo "服务已启动! 日志输出在 app.log"
