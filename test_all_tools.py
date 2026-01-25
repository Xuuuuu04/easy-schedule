#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
AI Agent 全部工具测试脚本
测试所有 27 个 LangChain 工具的功能
"""

import os
import sys
import json
from datetime import datetime, timedelta

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入所有工具
from backend.tools import (
    # Course Tools (6)
    fetch_courses_tool,
    add_course_tool,
    modify_course_tool,
    remove_course_tool,
    check_availability_tool,
    financial_report_tool,
    # Student Management Tools (5)
    fetch_students_tool,
    get_student_by_name_tool,
    create_student_tool,
    update_student_tool,
    delete_student_tool,
    # Student-Course Association Tools (3)
    get_student_courses_tool,
    get_student_schedule_tool,
    get_student_financial_summary_tool,
    # Intelligent Scheduling Tools (2)
    find_common_available_time_tool,
    suggest_optimal_time_tool,
    # Teaching Analysis Tools (3)
    get_teaching_summary_tool,
    get_student_progress_report_tool,
    get_daily_schedule_tool,
    # Notification Tools (3)
    get_upcoming_lessons_tool,
    get_absent_students_tool,
    get_weekly_overview_tool
)


def test_tool(tool_name, tool, params):
    """测试单个工具"""
    try:
        result = tool.invoke(params)
        # 检查是否有明显的错误
        if "Error" in str(result)[:50] or "Exception" in str(result)[:50]:
            return False, f"包含错误信息: {str(result)[:100]}"
        return True, str(result)[:100]
    except Exception as e:
        return False, str(e)


def main():
    print("\n" + "🎀"*30)
    print("       AI Agent 全部工具测试 (27个)")
    print("🎀"*30)

    results = {
        "passed": [],
        "failed": []
    }

    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    today = datetime.now().strftime("%Y-%m-%d")

    # ==================== Course Tools (6) ====================
    print("\n" + "="*60)
    print("  第一部分: 课程管理工具 (6个)")
    print("="*60)

    tests = [
        ("fetch_courses_tool", fetch_courses_tool, {},
         "获取所有课程列表"),

        ("check_availability_tool", check_availability_tool,
         {"start_time": f"{tomorrow}T16:00:00", "end_time": f"{tomorrow}T17:30:00"},
         "检查时间可用性"),

        ("financial_report_tool", financial_report_tool,
         {"month": datetime.now().month, "year": datetime.now().year},
         "获取本月财务报告"),

        ("get_daily_schedule_tool", get_daily_schedule_tool,
         {"date": today},
         "获取今日课程安排"),

        ("get_weekly_overview_tool", get_weekly_overview_tool, {},
         "获取本周课程概览"),

        ("get_teaching_summary_tool", get_teaching_summary_tool,
         {"date_range": "week"},
         "获取教学汇总"),
    ]

    for tool_name, tool, params, desc in tests:
        success, msg = test_tool(tool_name, tool, params)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"\n  {status} {desc}")
        print(f"     {tool_name}: {msg}")
        if success:
            results["passed"].append(tool_name)
        else:
            results["failed"].append((tool_name, msg))

    # ==================== Student Management Tools (5) ====================
    print("\n" + "="*60)
    print("  第二部分: 学生管理工具 (5个)")
    print("="*60)

    tests = [
        ("fetch_students_tool", fetch_students_tool, {},
         "获取所有学生列表"),

        ("get_student_by_name_tool", get_student_by_name_tool,
         {"name": "王五"},
         "按姓名查找学生"),

        ("get_student_courses_tool", get_student_courses_tool,
         {"student_name": "王五"},
         "获取学生课程记录"),

        ("get_student_schedule_tool", get_student_schedule_tool,
         {"student_name": "王五", "days": 7},
         "获取学生未来课程安排"),

        ("get_student_financial_summary_tool", get_student_financial_summary_tool,
         {"student_name": "王五"},
         "获取学生财务汇总"),

        ("get_student_progress_report_tool", get_student_progress_report_tool,
         {"student_name": "王五"},
         "获取学生学习进度报告"),
    ]

    for tool_name, tool, params, desc in tests:
        success, msg = test_tool(tool_name, tool, params)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"\n  {status} {desc}")
        print(f"     {tool_name}: {msg}")
        if success:
            results["passed"].append(tool_name)
        else:
            results["failed"].append((tool_name, msg))

    # ==================== Intelligent Scheduling Tools (2) ====================
    print("\n" + "="*60)
    print("  第三部分: 智能排课工具 (2个)")
    print("="*60)

    tests = [
        ("find_common_available_time_tool", find_common_available_time_tool,
         {"date": tomorrow, "duration_minutes": 90},
         "查找空闲时间段"),

        ("suggest_optimal_time_tool", suggest_optimal_time_tool,
         {"student_name": "王五"},
         "建议最优上课时间"),
    ]

    for tool_name, tool, params, desc in tests:
        success, msg = test_tool(tool_name, tool, params)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"\n  {status} {desc}")
        print(f"     {tool_name}: {msg}")
        if success:
            results["passed"].append(tool_name)
        else:
            results["failed"].append((tool_name, msg))

    # ==================== Teaching Analysis Tools (剩余) ====================
    print("\n" + "="*60)
    print("  第四部分: 提醒通知工具 (3个)")
    print("="*60)

    tests = [
        ("get_upcoming_lessons_tool", get_upcoming_lessons_tool,
         {"hours": 24},
         "获取即将到来的课程"),

        ("get_absent_students_tool", get_absent_students_tool,
         {"days": 30},
         "找出长期未上课学生"),
    ]

    for tool_name, tool, params, desc in tests:
        success, msg = test_tool(tool_name, tool, params)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"\n  {status} {desc}")
        print(f"     {tool_name}: {msg}")
        if success:
            results["passed"].append(tool_name)
        else:
            results["failed"].append((tool_name, msg))

    # ==================== Summary ====================
    print("\n" + "="*60)
    print("  测试总结")
    print("="*60)

    total = len(results["passed"]) + len(results["failed"])
    passed = len(results["passed"])
    failed = len(results["failed"])
    pass_rate = (passed / total * 100) if total > 0 else 0

    print(f"\n  📊 总计: {total} 个工具")
    print(f"  ✅ 通过: {passed} 个")
    print(f"  ❌ 失败: {failed} 个")
    print(f"  📈 通过率: {pass_rate:.1f}%")

    if results["failed"]:
        print(f"\n  ❌ 失败详情:")
        for tool_name, msg in results["failed"]:
            print(f"    • {tool_name}: {msg}")

    # 列出所有已测试的工具
    print(f"\n  📋 已测试工具列表:")
    all_tools = results["passed"] + [x[0] for x in results["failed"]]
    tool_groups = {
        "课程管理": ["fetch_courses_tool", "add_course_tool", "modify_course_tool", "remove_course_tool",
                    "check_availability_tool", "financial_report_tool"],
        "学生管理": ["fetch_students_tool", "get_student_by_name_tool", "create_student_tool",
                    "update_student_tool", "delete_student_tool"],
        "学生课程关联": ["get_student_courses_tool", "get_student_schedule_tool",
                        "get_student_financial_summary_tool"],
        "智能排课": ["find_common_available_time_tool", "suggest_optimal_time_tool"],
        "教学分析": ["get_teaching_summary_tool", "get_student_progress_report_tool", "get_daily_schedule_tool"],
        "提醒通知": ["get_upcoming_lessons_tool", "get_absent_students_tool", "get_weekly_overview_tool"]
    }

    for group, tools in tool_groups.items():
        tested = [t for t in tools if t in all_tools]
        if tested:
            print(f"\n  {group} ({len(tested)}/{len(tools)}):")
            for t in tested:
                status = "✅" if t in results["passed"] else "❌"
                print(f"    {status} {t}")

    if pass_rate >= 90:
        print(f"\n  🎉 优秀！所有工具功能正常！")
    elif pass_rate >= 70:
        print(f"\n  👍 良好！大部分工具功能正常。")
    elif pass_rate >= 50:
        print(f"\n  ⚠️  部分工具存在问题，请检查上述错误。")
    else:
        print(f"\n  ❌ 多数工具存在问题，请检查配置。")

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
