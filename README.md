# 课程表排课助手 (EasySchedule) 📅

一个基于 FastAPI + LangGraph + MySQL 的智能课程排课助手，专为教师和培训机构设计。

## ✨ 核心特性

- **可视化日历**: 基于 FullCalendar 的拖拽式课程管理。
- **AI 智能助手**: 集成 SiliconFlow/DeepSeek 大模型，支持自然语言排课。
  - "帮我给张三排一节周三下午3点的数学课"
  - "下周二晚上有空吗？"
  - "统计一下上个月的收入"
- **深度思考**: AI 具备思维链 (Chain of Thought) 能力，操作前先规划。
- **冲突检测**: 自动检测课程时间冲突，避免撞课。
- **财务统计**: 自动计算课时费收入。
- **学生档案**: 管理学生信息与学习进度。
- **Hello Kitty 主题**: 甜美温馨的 UI 设计，支持移动端适配。

## 🏗️ 技术架构

- **前端**: HTML5, CSS3 (Hello Kitty Theme), JavaScript (Vanilla), FullCalendar
- **后端**: Python 3.10+, FastAPI
- **数据库**: MySQL 8.0 (使用 SQLAlchemy ORM)
- **AI 引擎**: LangGraph + LangChain + SiliconFlow API (DeepSeek/GLM)

## 🚀 快速开始

### 1. 环境准备
- Python 3.10+
- MySQL 数据库

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置环境变量
复制 `.env.example` 为 `.env` 并填入配置：
```bash
# Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_password
DB_NAME=schedule_db

# AI / LLM (SiliconFlow)
SILICON_FLOW_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
SILICON_FLOW_BASE_URL=https://api.siliconflow.cn/v1
SILICON_FLOW_MODEL_NAME=deepseek-ai/DeepSeek-V3
```

### 4. 启动服务
```bash
python -m backend.main
```
访问 `http://localhost:9001` 即可使用。

## 📦 部署指南 (Linux/Server)

本项目的 `deploy/` 目录包含标准化的部署脚本，推荐使用以下流程。

### 1. 首次部署

```bash
# 1. 克隆代码
git clone git@gitcode.com:mumu_xsy/easyschedule.git
cd easyschedule

# 2. 数据库初始化 (解决权限问题)
# 请确保 MySQL 服务已启动。将创建专用用户 schedule_user。
# 需要输入 root 密码
sudo mysql < deploy/init_db.sql

# 3. 配置环境变量
cp .env.example .env
vim .env
# 确保填写:
# DB_USER=schedule_user
# DB_PASSWORD=schedule_pass_2024
# DB_NAME=schedule_db
# 以及 SILICON_FLOW_API_KEY

# 4. 启动服务
chmod +x deploy/update.sh
./deploy/update.sh
```

### 2. 更新部署 (日常维护)

当本地代码修改并推送后，在服务器执行：

```bash
./deploy/update.sh
```
该脚本会自动拉取代码、更新依赖并重启服务。

## 🛠️ AI 工具集

系统内置了以下 AI 工具，支持通过自然语言调用：
- `get_student_by_name_tool`: 查询学生信息
- `create_student_tool`: 创建学生档案
- `add_course_tool`: 添加单节课程
- `add_recurring_course_tool`: 批量添加周期性课程
- `modify_course_tool`: 修改课程时间/价格
- `remove_course_tool`: 删除课程
- `check_availability_tool`: 查询空闲时间
- `financial_report_tool`: 生成收入报表

## 📄 许可证

MIT License
