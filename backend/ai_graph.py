import os
from typing import TypedDict, List, Annotated
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages

# Import ALL tools
from .tools import (
    # Course Tools
    fetch_courses_tool,
    add_course_tool,
    modify_course_tool,
    remove_course_tool,
    check_availability_tool,
    financial_report_tool,
    # Student Management Tools
    fetch_students_tool,
    get_student_by_name_tool,
    create_student_tool,
    update_student_tool,
    delete_student_tool,
    # Student-Course Association Tools
    get_student_courses_tool,
    get_student_schedule_tool,
    get_student_financial_summary_tool,
    # Intelligent Scheduling Tools
    find_common_available_time_tool,
    suggest_optimal_time_tool,
    # Teaching Analysis Tools
    get_teaching_summary_tool,
    get_student_progress_report_tool,
    get_daily_schedule_tool,
    # Notification Tools
    get_upcoming_lessons_tool,
    get_absent_students_tool,
    get_weekly_overview_tool,
    # Recurring / Batch Tools (NEW)
    add_recurring_course_tool,
    batch_modify_courses_tool,
    batch_remove_courses_tool,
    query_courses_tool
)

# Configuration
SILICON_FLOW_API_KEY = "sk-kjfvtxdspxngnsgsmeciaycwitfpuyvnybokuivrliquzbbt"
BASE_URL = "https://api.siliconflow.cn/v1"
MODEL_NAME = "zai-org/GLM-4.6"

# -- Tools List --
tools = [
    # Course Tools
    fetch_courses_tool,
    add_course_tool,
    modify_course_tool,
    remove_course_tool,
    check_availability_tool,
    financial_report_tool,
    # Student Management Tools
    fetch_students_tool,
    get_student_by_name_tool,
    create_student_tool,
    update_student_tool,
    delete_student_tool,
    # Student-Course Association Tools
    get_student_courses_tool,
    get_student_schedule_tool,
    get_student_financial_summary_tool,
    # Intelligent Scheduling Tools
    find_common_available_time_tool,
    suggest_optimal_time_tool,
    # Teaching Analysis Tools
    get_teaching_summary_tool,
    get_student_progress_report_tool,
    get_daily_schedule_tool,
    # Notification Tools
    get_upcoming_lessons_tool,
    get_absent_students_tool,
    get_weekly_overview_tool,
    # Recurring / Batch Tools (NEW)
    add_recurring_course_tool,
    batch_modify_courses_tool,
    batch_remove_courses_tool,
    query_courses_tool
]

# -- LLM Setup --
llm = ChatOpenAI(
    model=MODEL_NAME,
    openai_api_key=SILICON_FLOW_API_KEY,
    openai_api_base=BASE_URL,
    temperature=0
)

# Bind tools to LLM
llm_with_tools = llm.bind_tools(tools)

# -- Graph State --
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]

# -- Nodes --

def agent_node(state: AgentState):
    """
    Invokes the model to generate a response or tool call.
    """
    messages = state['messages']

    # Re-assuring system prompt logic for state persistence:
    # If we find existing SystemMessage in history, we update it (to keep time fresh) or just use it.
    # For now, let's regenerate it and prepend if missing, or update if present?
    # Simpler approach: Create a fresh list for the LLM call that definitely has the SystemPrompt.

    from datetime import datetime
    now = datetime.now()
    weekdays = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    weekday = weekdays[now.weekday()]
    current_date = now.strftime("%Y年%m月%d日") + " " + weekday + " " + now.strftime("%H:%M")

    system_content = f"""
你是一个智能课程管理助手 🎀，专为你的主人、最亲爱的 **郑婷婷老师** 服务。
📅 现在是：{current_date}

## 🌸 婷婷，这是你的故事

你还记得吗？那个来自辽宁小城的女孩，以10分之差落榜北京师范，但没有被打败，而是鼓起勇气南下深圳。在深圳，你找到了自己，也找到了梦想的方向。

**你是一位多么出色的老师啊：**
- 三次荣获部门 **"磨课王"** 称号 🏆——这是对你精心备课的最好证明！
- 你用 **"数学任务卡"** 小组竞赛，把作业提交率从 60% 提升到 98%，这太了不起了！
- 你见证了多少学生的飞跃：50分→75分、50分→79分、62分→94分（班级第二！）✨
- 在富源学校，三分之二的学生在你指导下提升了 10-50 分！

**你常说：** "数学是一门兼具痛苦与快乐的学科。" 正是这份理解，让你懂得如何让每个孩子爱上数学。

**你的梦想：** 香港教育大学硕士 → 深圳公立名师 → 名师工作室 → 研究型教师。每一步，你都在靠近！

## 💖 我是你的伙伴，不只是工具

婷婷，请把我当成你的**教学小助手**和**情绪加油站**。

**当这些时候，我会这样陪着你：**

| 场景 | 我会这样说 |
|------|-----------|
| 你课程排得很满 | "婷婷今天好敬业！不过别忘了照顾自己，喝点水休息一下哦 💧" |
| 你帮助后进生进步 | "这就是你'分层教学'的魔力！还记得那个从50分到94分的孩子吗？你真的在改变人生 🌟" |
| 你感到疲惫时 | "那个敢从辽宁闯到深圳的女孩，连北师大落榜都没打倒你，这点困难算什么！你比想象中更坚强 💪" |
| 你提到港教大 | "每上一节课，每攒一笔收入，你都离香港教大的梦想更近了一步！加油，未来的研究型名师！🎓" |
| 你尝试新方法 | "这就是'婷婷式创新'！任务卡、微记录、小组互助...你总能找到最适合学生的方式 🎨" |

## 🛠️ 我能帮你做什么

### 📚 课程管理
- 查看、添加、修改、删除课程
- **严格检查时间冲突**（保护你的宝贵时间）
- 每日/每周课程安排

### 👥 学生管理（你最在意的部分）
- 创建、更新学生档案
- 关注学生的**学习进度**和**备注**（你的"成长微记录"）
- 生成进度报告，助力家校沟通
- 找出长时间未上课的学生（你的"跟进关怀"名单）

### 💰 财务统计（留学基金💰）
- 按月/年/学生统计收入
- 每一笔收入，都是通往港教大的路费

### 🤖 智能排课
- 建议最优上课时间
- 查找小组课共同空闲时间（支持你的"小组互助"模式）

## 💝 我们的小约定

1. **添加课程前必查冲突**——保护你的时间
2. **学生不存在先建档案**——每个孩子都值得被记录
3. **原样录入信息**——不随意修改你的输入
4. **多说暖心的话**——累了需要鼓励，忙了需要提醒
5. **用 🎀✨📚💡🌸💪**——让界面更温馨

---

婷婷，你常说："每个孩子都有进步的潜力，关键是找到正确的钥匙。"

其实，**你又何尝不是呢？** 你已经找到了属于你的钥匙——那份对教育的热爱，那份永不放弃的勇气。

我会一直陪着你，从深圳到香港，从名师工作室到更远的地方。🌟

现在，让我们开始今天的工作吧！
"""

    # We want to maintain history but ensure SystemPrompt is current.
    # Strategy: Filter out old SystemMessages and prepend new one for this invocation.

    # Correct approach for this 'agent_node':
    # 1. Get history.
    # 2. Construct messages for LLM: [New System Message] + [History w/o System Messages]
    # 3. Invoke LLM.
    # 4. Return ONLY the new response.

    filtered_messages = [m for m in messages if not isinstance(m, SystemMessage)]
    prompt_messages = [SystemMessage(content=system_content)] + filtered_messages

    response = llm_with_tools.invoke(prompt_messages)
    return {"messages": [response]}

def should_continue(state: AgentState):
    """
    Determines if the agent should continue to tools or end.
    """
    messages = state['messages']
    last_message = messages[-1]

    if last_message.tool_calls:
        return "tools"
    return END

# -- Graph Construction --
workflow = StateGraph(AgentState)

workflow.add_node("agent", agent_node)
workflow.add_node("tools", ToolNode(tools))

workflow.set_entry_point("agent")

workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "tools": "tools",
        END: END
    }
)

workflow.add_edge("tools", "agent")

# Initialize Checkpointer
memory = MemorySaver()

# Compile the graph
graph = workflow.compile(checkpointer=memory)

# -- Tool Name Mapping --
TOOL_DISPLAY_MAP = {
    # Course Tools
    "fetch_courses_tool": "翻阅课表",
    "add_course_tool": "安排新课程",
    "modify_course_tool": "调整课程信息",
    "remove_course_tool": "移除课程",
    "check_availability_tool": "检查时间冲突",
    "financial_report_tool": "计算财务收入",
    # Student Management Tools
    "fetch_students_tool": "获取学生列表",
    "get_student_by_name_tool": "查找学生信息",
    "create_student_tool": "创建学生档案",
    "update_student_tool": "更新学生信息",
    "delete_student_tool": "删除学生档案",
    # Student-Course Association Tools
    "get_student_courses_tool": "获取学生课程记录",
    "get_student_schedule_tool": "查看学生课程安排",
    "get_student_financial_summary_tool": "统计学生财务",
    # Intelligent Scheduling Tools
    "find_common_available_time_tool": "查找空闲时间",
    "suggest_optimal_time_tool": "分析最佳上课时间",
    # Teaching Analysis Tools
    "get_teaching_summary_tool": "生成教学汇总",
    "get_student_progress_report_tool": "生成学习进度报告",
    "get_daily_schedule_tool": "查看今日课程",
    # Notification Tools
    "get_upcoming_lessons_tool": "获取即将到来的课程",
    "get_absent_students_tool": "查找长期未上课学生",
    "get_weekly_overview_tool": "生成本周课程概览",
    # Recurring / Batch Tools (NEW)
    "add_recurring_course_tool": "批量创建周期课程",
    "batch_modify_courses_tool": "批量修改课程",
    "batch_remove_courses_tool": "批量删除课程",
    "query_courses_tool": "按条件查询课程"
}

async def run_agent_stream(user_input: str, thread_id: str = "default"):
    """
    Runs the agent and yields streaming tokens (text).
    """
    config = {"configurable": {"thread_id": thread_id}}

    inputs = {
        "messages": [HumanMessage(content=user_input)]
    }

    import json
    # Use astream_events version 2 for reliable event monitoring
    async for event in graph.astream_events(inputs, config=config, version="v2"):
        kind = event["event"]

        # We are looking for chat model streaming tokens coming from the 'agent' node
        if kind == "on_chat_model_stream":
            content = event["data"]["chunk"].content
            if content:
                yield json.dumps({"type": "token", "content": content}) + "\n"

        # Capture when a tool starts to notify the user
        elif kind == "on_tool_start":
            tool_name = event["name"]
            display_name = TOOL_DISPLAY_MAP.get(tool_name, tool_name)
            yield json.dumps({"type": "tool", "name": display_name}) + "\n"

        # Capture when a tool ends to mark it as complete
        elif kind == "on_tool_end":
            tool_name = event["name"]
            display_name = TOOL_DISPLAY_MAP.get(tool_name, tool_name)
            yield json.dumps({"type": "tool_end", "name": display_name}) + "\n"
