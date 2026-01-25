[根目录](../CLAUDE.md) > **frontend**

---

# Frontend 模块

课程表排课助手的前端界面，采用 Hello Kitty 粉色主题设计。

## 模块职责

- 日历视图展示与交互
- 课程 CRUD 弹窗操作
- AI 智能助手聊天面板
- 响应式布局（桌面/移动端）

## 入口与启动

**主入口**: `index.html`

前端由 FastAPI 静态文件服务托管，启动后端后访问: `http://localhost:9001`

## 对外接口（与后端交互）

### API 调用

```javascript
// 获取课程列表
GET /api/courses

// 创建课程
POST /api/courses
Body: { course_name, student_name, start_time, end_time, price }

// 更新课程
PUT /api/courses/{id}
Body: { course_name, student_name, start_time, end_time, price }

// 删除课程
DELETE /api/courses/{id}

// AI 对话
POST /api/ai/chat
Body: { message }
Response: SSE 流式 JSON
```

## 关键依赖与配置

### 外部 CDN

- **FullCalendar 6.1.10** - 日历组件
- **Marked.js** - Markdown 渲染
- **Google Fonts** - Noto Sans SC (中文), Quicksand (英文)

### 配置项

| 配置 | 默认值 | 说明 |
|------|--------|------|
| 服务端口 | 9001 | 后端服务端口 |
| 侧边栏宽度 | 340px | 桌面端 AI 面板宽度 |
| 日历开始时间 | 08:00 | 每日显示起始时间 |
| 日历结束时间 | 22:00 | 每日显示结束时间 |

## 界面组件

### 1. 日历组件 (FullCalendar)

- **视图模式**: 月视图 / 周视图 / 日视图 / 列表视图
- **交互**: 拖拽移动、拉伸调整时长、点击编辑
- **冲突显示**: 红色边框 + 抖动动画

### 2. AI 聊天面板

- **流式响应**: SSE 解析 JSON 格式数据
- **工具调用显示**: 旋转图标提示当前操作
- **Markdown 渲染**: 支持 AI 输出富文本

### 3. 课程编辑弹窗

- 支持新增和编辑两种模式
- 字段: 课程名称、学生姓名、开始/结束时间、价格
- 操作: 创建 / 保存修改 / 删除

## 样式主题

### Hello Kitty 粉色系

```css
--primary-color: #ED0D92;      /* 主色：蝴蝶粉 */
--primary-hover: #D10984;      /* 悬停色 */
--bg-color: #FFF0F5;           /* 背景粉 */
--sidebar-bg: #FFFFFF;         /* 侧边栏白 */
--border-color: #FADADD;       /* 边框淡粉 */
```

### 响应式断点

- **Desktop**: >= 1024px - 侧边栏常驻
- **Mobile**: < 1024px - 侧边栏隐藏，点击展开

## 模块文件说明

| 文件 | 行数 | 功能描述 |
|------|------|---------|
| `index.html` | 155 | 页面结构、SVG 装饰、弹窗容器 |
| `script.js` | 514 | 日历初始化、API 调用、聊天逻辑、事件处理 |
| `style.css` | 877 | 全局样式、组件样式、响应式布局 |

## 功能流程

### 添加课程流程

1. 点击「添加课程」按钮
2. 弹出编辑弹窗（默认下一小时时段）
3. 填写课程信息
4. 提交创建 -> 调用 POST /api/courses
5. 刷新日历显示

### AI 聊天流程

1. 用户输入消息
2. 发送 POST /api/ai/chat
3. 解析 SSE 流式响应
4. token 类型 -> 累积文本 + Markdown 渲染
5. tool 类型 -> 显示工具调用提示
6. 结束后刷新日历（如有变更）

## 常见问题

### Q: 为什么日历不显示？

确保后端服务已启动，检查浏览器控制台是否有 API 请求失败。

### Q: AI 回复乱码？

检查 `marked.js` CDN 是否加载成功，确保返回的是有效的 JSON 格式。

### Q: 拖拽课程后没有保存？

这是已知的 UI 同步问题，后端可能需要更新字段名称映射（`course_name` vs `title`）。

## 相关文件清单

```
frontend/
├── index.html    # 页面结构
├── script.js     # 交互逻辑
└── style.css     # 样式表
```

## 变更记录

### 2026-01-25
- 初始化模块文档
- 整理组件结构和 API 交互
