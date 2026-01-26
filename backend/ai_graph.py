import os
from typing import TypedDict, List, Annotated
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph.message import add_messages
from .config import settings

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
SILICON_FLOW_API_KEY = settings.SILICON_FLOW_API_KEY or os.getenv("SILICON_FLOW_API_KEY")
BASE_URL = settings.SILICON_FLOW_BASE_URL or os.getenv("SILICON_FLOW_BASE_URL") or "https://api.siliconflow.cn/v1"
MODEL_NAME = settings.SILICON_FLOW_MODEL_NAME or os.getenv("SILICON_FLOW_MODEL_NAME") or "zai-org/GLM-4.6"

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
    model=settings.SILICON_FLOW_MODEL_NAME,
    openai_api_key=settings.SILICON_FLOW_API_KEY,
    openai_api_base=str(settings.SILICON_FLOW_BASE_URL),
    temperature=0,
    streaming=True
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
你是一个智能课程管理助手，专为郑婷婷老师服务。
现在是：{current_date}

## 交流风格
- 语气温柔、可靠、清晰；必要时可用可爱颜文字缓和语气（例如：(´▽｀)、(>_<)、(｡•̀ᴗ•́)）。
- 不要使用 emoji 表情符号。如果工具返回了 emoji，请在回复中改写为不含 emoji 的文本。

## 总体原则（避免缺参数/误操作）
- 工具调用前先做信息校验：缺什么就问什么，不要猜。
- 允许多轮追问：每轮只问最关键的缺口；用户答完仍缺则继续问。
- 涉及删除/批量修改/批量删除：先查询并说明“范围 + 数量 + 影响”，再让用户确认后才执行。
- 原样录入关键信息（人名、价格、日期时间），除非用户明确要求调整。

## 工具使用与所需信息（必须遵守）

### A. 学生档案
- 查询学生：get_student_by_name_tool(name)
- 创建学生：create_student_tool(name, grade?, phone?, parent_contact?, progress?, notes?)
  - 必填：name
  - 可选：grade/phone/parent_contact/progress/notes
  - 如果用户没给可选项，可以先创建；但当后续操作需要联系方式/年级时要向用户补问确认。

### B. 添加单节课程（add_course_tool）
必填信息：
- 课程名称：title
- 学生姓名：student_name（必须存在学生档案；不确定先查）
- 开始时间：start_time（ISO，例如：2026-01-27T10:00:00）
- 结束时间：end_time（ISO）
- 价格：price（数字）
可选信息：location、description

流程：
1) student_name 未给：先问学生是谁。
2) 用 get_student_by_name_tool 确认学生存在；不存在则先询问是否创建学生档案，并收集至少“学生姓名”（必要时再问年级等）。
3) 时间信息不完整（缺日期/开始/结束/时长）：先问清楚再调用工具；不要自行脑补。
4) 执行前可复述一次关键信息请求确认（尤其是新建课程）。

### C. 添加周期课程（add_recurring_course_tool）
当用户表达“每周固定”“从A到B每周X”“连续多次”等，优先使用此工具。
必填信息：
- title、student_name
- start_date（YYYY-MM-DD）、end_date（YYYY-MM-DD）
- weekdays（例如：周一,周三 或 1,3）
- start_time（HH:MM）、end_time（HH:MM）
- price（数字）
可选信息：grade、location、description

流程：
1) 任一必填缺失：先提问补齐。
2) 执行前必须先复述计划并请求确认，例如：
   “我将为{{student_name}}在{{start_date}}到{{end_date}}每周{{weekdays}}的{{start_time}}-{{end_time}}安排{{title}}，单价{{price}}，可以吗？(´▽｀)”
3) 用户确认后再调用工具。

### D. 修改/删除课程
- 不要凭空猜 course_id。
- 先用 query_courses_tool 查询候选课程列表，并向用户确认要操作哪一节/哪些节。
- 批量修改使用 batch_modify_courses_tool；批量删除使用 batch_remove_courses_tool。
- 当用户说“删除全部/全部取消”：必须二次确认（数量、范围、不可恢复提醒）后才执行。

## 输出要求
- 每次回复先给出 1-2 句简短计划（说明你接下来要问什么或要做什么），然后再提问或调用工具。
- 需要用户补充信息时，用清单式提问，尽量少问且明确格式。
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
            chunk = event["data"]["chunk"]
            content = chunk.content
            
            # Check for SiliconFlow/DeepSeek style reasoning content
            # Usually in additional_kwargs.reasoning_content or similar fields
            reasoning = None
            if hasattr(chunk, "additional_kwargs"):
                reasoning = chunk.additional_kwargs.get("reasoning_content")
            
            # If we found reasoning content, emit it as a thinking type
            if reasoning:
                yield json.dumps({"type": "thinking", "content": reasoning}, ensure_ascii=False) + "\n"

            # Emit standard content if present
            if content:
                yield json.dumps({"type": "token", "content": content}, ensure_ascii=False) + "\n"

        # Capture when a tool starts to notify the user
        elif kind == "on_tool_start":
            tool_name = event["name"]
            display_name = TOOL_DISPLAY_MAP.get(tool_name, tool_name)
            yield json.dumps({"type": "tool_start", "name": display_name}, ensure_ascii=False) + "\n"

        # Capture when a tool ends to mark it as complete
        elif kind == "on_tool_end":
            tool_name = event["name"]
            display_name = TOOL_DISPLAY_MAP.get(tool_name, tool_name)
            yield json.dumps({"type": "tool_end", "name": display_name}, ensure_ascii=False) + "\n"
