[根目录](../CLAUDE.md) > **backend**

---

# Backend 模块

基于 FastAPI 的后端服务模块，提供课程 CRUD API 和 AI 智能对话功能。

## 模块职责

- RESTful API 服务（课程管理）
- AI 对话流式响应接口
- LangGraph Agent 工具编排
- 数据持久化（JSON 文件）

## 入口与启动

**主入口**: `main.py`

```bash
# 直接运行
python -m backend.main

# 或使用 uvicorn
uvicorn backend.main:app --host 0.0.0.0 --port 9001 --reload
```

启动后访问: `http://localhost:9001`

## 对外接口

### REST API

| 方法 | 路径 | 功能 | 请求体 |
|------|------|------|--------|
| GET | `/api/courses` | 列出所有课程 | - |
| POST | `/api/courses` | 创建课程 | `CourseCreate` |
| PUT | `/api/courses/{id}` | 更新课程 | `CourseUpdate` |
| DELETE | `/api/courses/{id}` | 删除课程 | - |

### AI Chat API

| 方法 | 路径 | 功能 |
|------|------|------|
| POST | `/api/ai/chat` | 流式 AI 对话 |

请求体: `{ "message": "用户消息" }`

## 关键依赖与配置

### requirements.txt

```
fastapi          # Web 框架
uvicorn          # ASGI 服务器
pydantic         # 数据验证
openai           # OpenAI API 客户端
python-multipart # 文件上传支持
langgraph        # Agent 框架
langchain        # LLM 基础框架
langchain_openai # OpenAI 兼容接口
```

### API 配置

位置: `ai_graph.py`

```python
SILICON_FLOW_API_KEY = "sk-***"
BASE_URL = "https://api.siliconflow.cn/v1"
MODEL_NAME = "zai-org/GLM-4.6"
```

## 数据模型

### Course (models.py)

```python
class Course(BaseModel):
    id: str                    # UUID
    title: str                 # 课程名称
    start: datetime            # 开始时间
    end: datetime              # 结束时间
    student_name: str          # 学生姓名
    price: float               # 价格
    color: str = "#F5A3C8"    # 显示颜色
    description: Optional[str] # 备注
```

## 模块文件说明

| 文件 | 行数 | 功能描述 |
|------|------|---------|
| `main.py` | 61 | FastAPI 应用入口、路由定义、静态文件挂载 |
| `models.py` | 34 | Pydantic 数据模型定义 |
| `service.py` | 101 | 课程 CRUD 业务逻辑、冲突检测 |
| `ai_service.py` | 20 | AI 对话流式响应封装 |
| `ai_graph.py` | 198 | LangGraph Agent 定义、工具绑定、流式输出 |
| `tools.py` | 143 | 6 个 AI 可调用工具函数 |

## 测试与质量

### 验证脚本

- `verify_context.py` - 验证 AI 对话上下文记忆功能

### 运行测试

```bash
python verify_context.py
```

## 常见问题

### Q: 如何更换 LLM 模型？

修改 `ai_graph.py` 中的 `MODEL_NAME` 和 `BASE_URL`，确保使用兼容 OpenAI API 格式的服务。

### Q: 数据存储在哪里？

默认存储在项目根目录的 `data/courses.json` 文件中。

### Q: 如何添加新的 AI 工具？

1. 在 `tools.py` 中用 `@tool` 装饰器定义函数
2. 在 `ai_graph.py` 的 `tools` 列表中注册
3. 重新启动服务

## 相关文件清单

```
backend/
├── __init__.py
├── __pycache__/      # Python 缓存（忽略）
├── main.py           # FastAPI 入口
├── models.py         # 数据模型
├── service.py        # 业务逻辑
├── ai_service.py     # AI 服务封装
├── ai_graph.py       # LangGraph Agent
└── tools.py          # AI 工具函数
```

## 变更记录

### 2026-01-25
- 初始化模块文档
- 整理 API 接口清单
