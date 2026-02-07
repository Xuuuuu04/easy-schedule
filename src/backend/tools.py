from datetime import datetime, timedelta
from typing import List, Optional
import json
import calendar

from langchain_core.tools import tool
from .service import (
    get_all_courses,
    create_course,
    update_course,
    delete_course,
    check_conflicts,
    get_all_students,
    get_student,
    get_student_by_name,
    create_student as service_create_student,
    update_student as service_update_student,
    delete_student as service_delete_student,
    query_courses_filtered,
    bulk_update_courses_filtered,
    bulk_delete_courses_filtered,
    bulk_create_recurring_courses,
    CourseCreate,
    CourseUpdate,
    StudentCreate,
    StudentUpdate
)
from .models import Course, Student

# ==================== Course Tools (Existing) ====================

@tool
def fetch_courses_tool() -> str:
    """获取所有课程列表，返回 JSON 格式"""
    courses = get_all_courses()
    return json.dumps([c.dict() for c in courses], default=str, ensure_ascii=False)

@tool
def add_course_tool(
    title: str,
    start_time: str,
    end_time: str,
    student_name: str,
    price: float,
    description: str = "",
    location: Optional[str] = None,
    color: str = "#F5A3C8"
) -> str:
    """
    添加新课程到日程表。
    start_time 和 end_time 必须是 ISO 格式 (例如: '2026-01-27T10:00:00')。
    返回创建的课程或错误信息。
    """
    try:
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)

        # 查找学生ID
        student = get_student_by_name(student_name)
        if not student:
            return f"错误：找不到学生 '{student_name}'，请先创建该学生档案。"

        course_in = CourseCreate(
            title=title,
            start=start,
            end=end,
            student_id=student.id,
            price=price,
            description=description,
            location=location,
            color=color
        )
        new_course = create_course(course_in)
        return f"✅ 成功添加课程: {new_course.title} - {student_name}，时间: {new_course.start.strftime('%Y-%m-%d %H:%M')}"
    except ValueError as e:
        return f"⚠️ 日期/时间解析错误: {str(e)}"
    except Exception as e:
        return f"⚠️ 添加课程时出错: {str(e)}"

@tool
def modify_course_tool(
    course_id: str,
    title: Optional[str] = None,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    student_name: Optional[str] = None,
    price: Optional[float] = None,
    description: Optional[str] = None,
    location: Optional[str] = None
) -> str:
    """
    修改现有课程，只提供需要更新的字段。
    start_time/end_time 必须是 ISO 字符串。
    """
    try:
        update_data = {}
        if title: update_data['title'] = title
        if start_time: update_data['start'] = datetime.fromisoformat(start_time)
        if end_time: update_data['end'] = datetime.fromisoformat(end_time)
        if price is not None: update_data['price'] = price
        if description is not None: update_data['description'] = description
        if location is not None: update_data['location'] = location

        # 如果更新学生姓名，需要查找学生ID
        if student_name:
            student = get_student_by_name(student_name)
            if not student:
                return f"⚠️ 错误：找不到学生 '{student_name}'"
            update_data['student_id'] = student.id

        course_in = CourseUpdate(**update_data)
        updated = update_course(course_id, course_in)
        if updated:
            return f"✅ 成功更新课程: {updated.title}"
        else:
            return f"⚠️ 课程 {course_id} 不存在"
    except Exception as e:
        return f"⚠️ 更新课程时出错: {str(e)}"

@tool
def remove_course_tool(course_id: str) -> str:
    """根据 ID 删除课程"""
    if delete_course(course_id):
        return f"✅ 成功删除课程 {course_id}"
    else:
        return f"⚠️ 课程 {course_id} 不存在"

@tool
def check_availability_tool(start_time: str, end_time: str) -> str:
    """
    检查时间段是否可用。
    如果有冲突，返回冲突的课程列表。
    """
    try:
        start = datetime.fromisoformat(start_time)
        end = datetime.fromisoformat(end_time)
        conflicts = check_conflicts(start, end)
        if conflicts:
            conflict_info = [f"{c.title} ({c.start.strftime('%Y-%m-%d %H:%M')}-{c.end.strftime('%H:%M')})" for c in conflicts]
            return f"⚠️ 检测到 {len(conflicts)} 个时间冲突:\n" + "\n".join(conflict_info)
        return "✅ 该时间段可用"
    except Exception as e:
        return f"⚠️ 检查可用性时出错: {str(e)}"

@tool
def financial_report_tool(month: Optional[int] = None, year: Optional[int] = None) -> str:
    """
    计算总收入。
    如果提供月份/年份，按该月/年筛选。
    否则返回全部时间的统计。
    """
    courses = get_all_courses()
    total = 0.0
    count = 0
    student_stats = {}

    target_month = month
    target_year = year or datetime.now().year

    for c in courses:
        should_include = True
        if month:
            if c.start.month == target_month and c.start.year == target_year:
                should_include = True
            else:
                should_include = False

        if should_include:
            total += c.price
            count += 1
            # 按学生统计
            student_name = c.student_name or "未知"
            if student_name not in student_stats:
                student_stats[student_name] = {"income": 0, "count": 0}
            student_stats[student_name]["income"] += c.price
            student_stats[student_name]["count"] += 1

    period = f"{target_year}年{target_month}月" if month else f"截止{target_year}年全部"
    result = f"📊 财务报告 ({period})\n"
    result += f"━━━━━━━━━━━━━━━━━━━━━━\n"
    result += f"💰 总收入: ¥{total:.0f}\n"
    result += f"📚 总课时: {count} 节\n"
    result += f"💵 平均单价: ¥{total/count if count > 0 else 0:.0f}\n\n"

    if student_stats:
        result += "📋 按学生统计:\n"
        sorted_students = sorted(student_stats.items(), key=lambda x: x[1]["income"], reverse=True)
        for name, stats in sorted_students:
            result += f"  • {name}: ¥{stats['income']:.0f} ({stats['count']}节)\n"

    return result

# ==================== Student Management Tools (NEW) ====================

@tool
def fetch_students_tool() -> str:
    """获取所有学生列表，返回 JSON 格式"""
    students = get_all_students()
    return json.dumps([s.dict() for s in students], ensure_ascii=False)

@tool
def get_student_by_name_tool(name: str) -> str:
    """根据姓名查找学生，返回学生详细信息（年级、联系方式、备注）"""
    student = get_student_by_name(name)
    if not student:
        return f"⚠️ 找不到学生 '{name}'"

    result = f"""👤 学生档案
━━━━━━━━━━━━━━━━━━━━━━
📛 姓名: {student.name}
📚 年级: {student.grade or '未设置'}
📱 电话: {student.phone or '未设置'}
👨‍👩‍👧 家长联系方式: {student.parent_contact or '未设置'}
📊 学习进度: {student.progress}%
📝 备注: {student.notes or '无'}
🆔 学生ID: {student.id}
"""
    return result

@tool
def create_student_tool(
    name: str,
    grade: str = "",
    phone: str = "",
    parent_contact: str = "",
    progress: int = 0,
    notes: str = ""
) -> str:
    """创建新学生档案"""
    try:
        student_in = StudentCreate(
            name=name,
            grade=grade if grade else None,
            phone=phone if phone else None,
            parent_contact=parent_contact if parent_contact else None,
            progress=progress,
            notes=notes if notes else None
        )
        new_student = service_create_student(student_in)
        return f"✅ 成功创建学生档案: {new_student.name} (ID: {new_student.id})"
    except Exception as e:
        return f"⚠️ 创建学生时出错: {str(e)}"

@tool
def update_student_tool(
    student_id: int,
    name: Optional[str] = None,
    grade: Optional[str] = None,
    phone: Optional[str] = None,
    parent_contact: Optional[str] = None,
    progress: Optional[int] = None,
    notes: Optional[str] = None
) -> str:
    """更新学生信息（进度、备注等）"""
    try:
        update_data = {}
        if name is not None: update_data['name'] = name
        if grade is not None: update_data['grade'] = grade
        if phone is not None: update_data['phone'] = phone
        if parent_contact is not None: update_data['parent_contact'] = parent_contact
        if progress is not None: update_data['progress'] = progress
        if notes is not None: update_data['notes'] = notes

        student_in = StudentUpdate(**update_data)
        updated = service_update_student(student_id, student_in)
        if updated:
            return f"✅ 成功更新学生信息: {updated.name}"
        else:
            return f"⚠️ 学生ID {student_id} 不存在"
    except Exception as e:
        return f"⚠️ 更新学生时出错: {str(e)}"

@tool
def delete_student_tool(student_id: int, student_name: str = "") -> str:
    """
    删除学生及其所有相关课程。
    student_name 用于确认删除。
    """
    try:
        student = get_student(student_id)
        if not student:
            return f"⚠️ 学生ID {student_id} 不存在"

        confirm_name = student_name if student_name else student.name
        success = service_delete_student(student_id)
        if success:
            return f"✅ 已删除学生 '{confirm_name}' 及其所有课程记录"
        else:
            return f"⚠️ 删除失败"
    except Exception as e:
        return f"⚠️ 删除学生时出错: {str(e)}"

# ==================== Student-Course Association Tools (NEW) ====================

@tool
def get_student_courses_tool(student_name: str) -> str:
    """获取某学生的所有课程记录"""
    student = get_student_by_name(student_name)
    if not student:
        return f"⚠️ 找不到学生 '{student_name}'"

    all_courses = get_all_courses()
    student_courses = [c for c in all_courses if c.student_id == student.id]

    if not student_courses:
        return f"📚 {student_name} 暂无课程记录"

    # 按时间排序
    student_courses.sort(key=lambda c: c.start)

    result = f"📚 {student_name} 的课程记录\n"
    result += f"━━━━━━━━━━━━━━━━━━━━━━\n"

    upcoming = []
    past = []
    now = datetime.now()

    for c in student_courses:
        course_info = f"  • {c.title} | {c.start.strftime('%Y-%m-%d %H:%M')}-{c.end.strftime('%H:%M')} | ¥{c.price}\n"
        if c.start >= now:
            upcoming.append(course_info)
        else:
            past.append(course_info)

    if upcoming:
        result += f"\n📅 即将到来 ({len(upcoming)}节):\n"
        result += "".join(upcoming)

    if past:
        result += f"\n📜 历史记录 ({len(past)}节):\n"
        result += "".join(past)

    total_income = sum(c.price for c in student_courses)
    result += f"\n💵 累计收入: ¥{total_income:.0f}"

    return result

@tool
def get_student_schedule_tool(student_name: str, days: int = 7) -> str:
    """获取某学生未来 N 天的课程安排"""
    student = get_student_by_name(student_name)
    if not student:
        return f"⚠️ 找不到学生 '{student_name}'"

    all_courses = get_all_courses()
    student_courses = [c for c in all_courses if c.student_id == student.id]

    now = datetime.now()
    end_date = now + timedelta(days=days)

    upcoming = [c for c in student_courses if now <= c.start <= end_date]
    upcoming.sort(key=lambda c: c.start)

    if not upcoming:
        return f"📅 {student_name} 在未来 {days} 天内暂无课程安排"

    result = f"📅 {student_name} 未来 {days} 天课程安排\n"
    result += f"━━━━━━━━━━━━━━━━━━━━━━\n"

    for c in upcoming:
        days_until = (c.start.date() - now.date()).days
        time_desc = "今天" if days_until == 0 else f"{days_until}天后" if days_until > 0 else ""
        result += f"📌 {c.title}\n"
        result += f"   📆 {c.start.strftime('%Y-%m-%d')} ({time_desc}) {c.start.strftime('%H:%M')}-{c.end.strftime('%H:%M')}\n"
        result += f"   💰 ¥{c.price}\n\n"

    return result

@tool
def get_student_financial_summary_tool(student_name: str) -> str:
    """获取某学生的累计收入统计"""
    student = get_student_by_name(student_name)
    if not student:
        return f"⚠️ 找不到学生 '{student_name}'"

    all_courses = get_all_courses()
    student_courses = [c for c in all_courses if c.student_id == student.id]

    if not student_courses:
        return f"💰 {student_name} 暂无收入记录"

    total_income = sum(c.price for c in student_courses)
    total_hours = sum((c.end - c.start).total_seconds() / 3600 for c in student_courses)
    avg_price = total_income / len(student_courses) if student_courses else 0

    # 本月统计
    now = datetime.now()
    this_month_courses = [c for c in student_courses if c.start.month == now.month and c.start.year == now.year]
    this_month_income = sum(c.price for c in this_month_courses)

    result = f"""💰 {student_name} 财务统计
━━━━━━━━━━━━━━━━━━━━━━
📊 累计收入: ¥{total_income:.0f}
📚 总课时: {len(student_courses)} 节
⏱️ 总时长: {total_hours:.1f} 小时
💵 平均单价: ¥{avg_price:.0f}
📅 本月收入: ¥{this_month_income:.0f} ({len(this_month_courses)}节)
🆔 学生ID: {student.id}
"""

    return result

# ==================== Intelligent Scheduling Tools (NEW) ====================

@tool
def find_common_available_time_tool(
    date: str,
    duration_minutes: int,
    student_names: Optional[List[str]] = None
) -> str:
    """
    查找指定日期的所有空闲时间段。
    如果提供多个学生姓名，返回所有人都空闲的时间段（用于小组课）。
    date 格式: YYYY-MM-DD
    """
    try:
        target_date = datetime.fromisoformat(date).date()
    except:
        return f"⚠️ 日期格式错误，请使用 YYYY-MM-DD 格式"

    # 定义课程时段范围 (8:00 - 22:00)
    day_start = datetime.combine(target_date, datetime.min.time()).replace(hour=8, minute=0)
    day_end = datetime.combine(target_date, datetime.min.time()).replace(hour=22, minute=0)

    # 获取所有课程
    all_courses = get_all_courses()

    # 筛选指定日期的课程
    day_courses = []
    for c in all_courses:
        if c.start.date() == target_date:
            # 如果指定了学生，只筛选这些学生的课程
            if student_names:
                student = get_student(c.student_id)
                if student and student.name in student_names:
                    day_courses.append(c)
            else:
                day_courses.append(c)

    if not day_courses:
        return f"✅ {date} 全天空闲，可随时安排 {duration_minutes} 分钟课程"

    # 找出所有空闲时段
    busy_slots = [(c.start, c.end) for c in day_courses]
    busy_slots.sort(key=lambda x: x[0])

    available_slots = []
    current_time = day_start

    for busy_start, busy_end in busy_slots:
        if current_time + timedelta(minutes=duration_minutes) <= busy_start:
            available_slots.append((current_time, busy_start))
        current_time = max(current_time, busy_end)

    # 检查最后一个时段
    if current_time + timedelta(minutes=duration_minutes) <= day_end:
        available_slots.append((current_time, day_end))

    if not available_slots:
        return f"⚠️ {date} 没有足够的连续 {duration_minutes} 分钟空闲时段"

    result = f"🕐 {date} 可用时段 (至少{duration_minutes}分钟):\n"
    result += "━━━━━━━━━━━━━━━━━━━━━━\n"

    for slot_start, slot_end in available_slots:
        duration = int((slot_end - slot_start).total_seconds() / 60)
        result += f"  • {slot_start.strftime('%H:%M')} - {slot_end.strftime('%H:%M')} (可用 {duration} 分钟)\n"

    return result

@tool
def suggest_optimal_time_tool(
    student_name: str,
    preferred_days: Optional[List[str]] = None
) -> str:
    """
    基于历史数据，建议最优上课时间。
    preferred_days: 偏好的星期列表，如 ["周一", "周二", "周三"]
    """
    student = get_student_by_name(student_name)
    if not student:
        return f"⚠️ 找不到学生 '{student_name}'"

    all_courses = get_all_courses()
    student_courses = [c for c in all_courses if c.student_id == student.id]

    if len(student_courses) < 3:
        return f"💡 {student_name} 的课程记录较少，建议多安排几次课程后再使用此功能"

    # 统计各时段的课程频率
    weekday_counts = {}  # 星期几
    hour_counts = {}     # 几点

    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

    for c in student_courses:
        weekday = c.start.weekday()  # 0=周一, 6=周日
        hour = c.start.hour

        weekday_counts[weekday] = weekday_counts.get(weekday, 0) + 1
        hour_counts[hour] = hour_counts.get(hour, 0) + 1

    # 找出最常上课的时间
    best_weekdays = sorted(weekday_counts.items(), key=lambda x: x[1], reverse=True)[:3]
    best_hours = sorted(hour_counts.items(), key=lambda x: x[1], reverse=True)[:3]

    result = f"""💡 {student_name} 的上课时间分析
━━━━━━━━━━━━━━━━━━━━━━

📅 最常上课的星期:
"""
    for weekday, count in best_weekdays:
        result += f"  • {weekday_names[weekday]}: {count} 节课\n"

    result += f"\n⏰ 最常上课的时间段:\n"
    for hour, count in best_hours:
        result += f"  • {hour:02d}:00 - {hour+1:02d}:00: {count} 节课\n"

    result += f"\n🎯 建议安排时间:\n"

    # 综合推荐
    suggestions = []
    for weekday, _ in best_weekdays[:2]:
        for hour, _ in best_hours[:2]:
            day_name = weekday_names[weekday]
            if not preferred_days or day_name in preferred_days:
                suggestions.append(f"  • {day_name} {hour:02d}:00-{hour+1:02d}:00")

    if suggestions:
        result += "\n".join(suggestions[:4])
    else:
        result += "  根据历史记录，" + "、".join([weekday_names[w] for w, _ in best_weekdays[:2]]) + " 的下午时段较为合适"

    return result

# ==================== Teaching Analysis Tools (NEW) ====================

@tool
def get_teaching_summary_tool(date_range: str = "week") -> str:
    """
    获取教学汇总。
    date_range: "week" (本周), "month" (本月), "all" (全部)
    """
    courses = get_all_courses()
    now = datetime.now()

    filtered_courses = []
    if date_range == "week":
        # 如果是周日(6)，则"本周"指向下一周（周一到周日）
        if now.weekday() == 6:
            week_start = now + timedelta(days=1)
        else:
            week_start = now - timedelta(days=now.weekday())
        week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
        week_end = week_start + timedelta(days=7)
        filtered_courses = [c for c in courses if week_start <= c.start < week_end]
        period_label = "本周"
    elif date_range == "month":
        filtered_courses = [c for c in courses if c.start.month == now.month and c.start.year == now.year]
        period_label = "本月"
    else:
        filtered_courses = courses
        period_label = "全部"

    if not filtered_courses:
        return f"📊 {period_label}暂无课程记录"

    total_income = sum(c.price for c in filtered_courses)
    total_hours = sum((c.end - c.start).total_seconds() / 3600 for c in filtered_courses)

    # 统计学生数
    unique_students = set(c.student_id for c in filtered_courses)

    # 按课程类型统计
    course_types = {}
    for c in filtered_courses:
        course_types[c.title] = course_types.get(c.title, 0) + 1

    result = f"""📊 {period_label}教学汇总
━━━━━━━━━━━━━━━━━━━━━━
📚 总课时: {len(filtered_courses)} 节
⏱️ 总时长: {total_hours:.1f} 小时
👥 学生数: {len(unique_students)} 人
💰 总收入: ¥{total_income:.0f}
💵 平均时薪: ¥{total_income/total_hours if total_hours > 0 else 0:.0f}
"""

    if course_types:
        result += f"\n📋 课程类型分布:\n"
        sorted_types = sorted(course_types.items(), key=lambda x: x[1], reverse=True)
        for course_type, count in sorted_types:
            result += f"  • {course_type}: {count} 节\n"

    return result

@tool
def get_student_progress_report_tool(student_name: str) -> str:
    """生成学生学习进度报告（结合课程频率、备注）"""
    student = get_student_by_name(student_name)
    if not student:
        return f"⚠️ 找不到学生 '{student_name}'"

    all_courses = get_all_courses()
    student_courses = [c for c in all_courses if c.student_id == student.id]

    if not student_courses:
        return f"📊 {student_name} 暂无学习记录"

    # 按时间排序
    student_courses.sort(key=lambda c: c.start, reverse=True)

    # 计算学习频率
    now = datetime.now()
    one_month_ago = now - timedelta(days=30)
    recent_courses = [c for c in student_courses if c.start >= one_month_ago]
    three_months_ago = now - timedelta(days=90)

    total_hours = sum((c.end - c.start).total_seconds() / 3600 for c in student_courses)

    # 最近一次上课
    last_lesson = student_courses[0] if student_courses else None
    days_since_last = (now - last_lesson.start).days if last_lesson else None

    result = f"""📊 {student_name} 学习进度报告
━━━━━━━━━━━━━━━━━━━━━━

📈 设定进度: {student.progress}%
📚 累计课时: {len(student_courses)} 节
⏱️ 累计时长: {total_hours:.1f} 小时
📅 近一月上课: {len(recent_courses)} 节
"""

    if days_since_last is not None:
        if days_since_last <= 7:
            result += f"🕐 最近上课: {days_since_last} 天前 (活跃)\n"
        elif days_since_last <= 30:
            result += f"🕐 最近上课: {days_since_last} 天前\n"
        else:
            result += f"⚠️ 最近上课: {days_since_last} 天前 (需要关注)\n"

    if student.notes:
        result += f"\n📝 学习备注:\n{student.notes}\n"

    # 最近课程记录
    if len(student_courses) > 0:
        result += f"\n📜 最近课程记录:\n"
        for c in student_courses[:5]:
            result += f"  • {c.start.strftime('%Y-%m-%d %H:%M')} {c.title} ¥{c.price}\n"

    return result

@tool
def get_daily_schedule_tool(date: Optional[str] = None) -> str:
    """获取指定日期的课程清单，不指定日期则返回今天"""
    if date:
        try:
            target_date = datetime.fromisoformat(date).date()
        except:
            return f"⚠️ 日期格式错误，请使用 YYYY-MM-DD 格式"
    else:
        target_date = datetime.now().date()

    all_courses = get_all_courses()
    day_courses = [c for c in all_courses if c.start.date() == target_date]
    day_courses.sort(key=lambda c: c.start)

    date_str = target_date.strftime("%Y年%m月%d日")
    weekday = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][target_date.weekday()]

    if not day_courses:
        return f"📅 {date_str} ({weekday})\n\n✅ 今天没有课程安排"

    total_income = sum(c.price for c in day_courses)
    total_hours = sum((c.end - c.start).total_seconds() / 3600 for c in day_courses)

    result = f"""📅 {date_str} ({weekday})
━━━━━━━━━━━━━━━━━━━━━━

"""

    for c in day_courses:
        result += f"🕐 {c.start.strftime('%H:%M')} - {c.end.strftime('%H:%M')}\n"
        result += f"   {c.title} | {c.student_name or '未知学生'}\n"
        result += f"   💰 ¥{c.price}\n\n"

    result += f"💵 今日收入: ¥{total_income:.0f} | ⏱️ 总时长: {total_hours:.1f}小时"

    return result

# ==================== Recurring / Batch Tools (NEW) ====================

@tool
def add_recurring_course_tool(
    title: str,
    student_name: str,
    start_date: str,
    end_date: str,
    weekdays: str,
    start_time: str,
    end_time: str,
    price: float,
    grade: str = "",  # 新增：年级，用于自动创建学生
    description: str = "",
    location: Optional[str] = None,
    color: str = "#F5A3C8"
) -> str:
    """
    【推荐】批量添加周期性课程（一次性创建多节重复课程）。
    当需要安排"每周固定时间"或"一段时间内多次课程"时，必须优先使用此工具，这比单次添加更高效且稳健。

    **功能增强**：如果学生不存在，会自动创建学生档案！

    参数说明:
    - title: 课程标题，如 "数学课"
    - student_name: 学生姓名
    - start_date: 开始日期，格式 "YYYY-MM-DD"，如 "2026-02-01"
    - end_date: 结束日期，格式 "YYYY-MM-DD"，如 "2026-05-01"
    - weekdays: 星期几，多个用逗号分隔。如: "周一,周三" 或 "1,3,5"
    - start_time: 上课时间，格式 "HH:MM"，如 "15:00"
    - end_time: 下课时间，格式 "HH:MM"，如 "17:00"
    - price: 每节课费用
    - grade: 学生年级（可选，如果学生不存在会用于创建档案）
    """
    try:
        stats = bulk_create_recurring_courses(
            title=title,
            student_name=student_name,
            start_date=start_date,
            end_date=end_date,
            weekdays=weekdays,
            start_time=start_time,
            end_time=end_time,
            price=price,
            grade=grade,
            description=description,
            location=location,
            color=color,
        )

        result = f"🎀 周期性课程创建完成！\n"
        result += f"━━━━━━━━━━━━━━━━━━━━━━\n"
        if stats.get("auto_created"):
            result += f"✨ 已自动创建学生档案: {student_name}\n"

        result += f"📚 课程: {title}\n"
        result += f"👤 学生: {student_name}"
        if stats.get("student_grade"):
            result += f" ({stats.get('student_grade')})"
        result += "\n"
        result += f"📅 时间范围: {start_date} ~ {end_date}\n"
        result += f"📆 每周: {weekdays}\n"
        result += f"⏰ 时段: {start_time}-{end_time}\n\n"

        created = int(stats.get("created") or 0)
        conflicts = stats.get("conflicts") or []
        months = stats.get("months") or {}

        if created > 0:
            result += f"✅ 成功创建: {created} 节课\n"
            for month in sorted(months.keys()):
                result += f"   {month}: {months[month]} 节\n"
            result += f"💰 预计收入: ¥{float(stats.get('expected_income') or 0):.0f}\n"
        else:
            result += f"⚠️ 未创建任何课程（可能全部冲突或日期范围内无匹配星期）\n"

        if conflicts:
            result += f"\n⚠️ 跳过冲突日期: {len(conflicts)} 个\n"
            for d in conflicts[:5]:
                result += f"   • {d} {start_time}\n"
            if len(conflicts) > 5:
                result += f"   ... 还有 {len(conflicts) - 5} 个\n"

        return result

    except ValueError as e:
        return f"⚠️ 日期/时间格式错误: {str(e)}"
    except Exception as e:
        return f"⚠️ 创建周期性课程时出错: {str(e)}"


@tool
def batch_modify_courses_tool(
    title_pattern: str = "",
    student_name: str = "",
    date_range: Optional[str] = None,
    weekday: Optional[str] = None,
    new_time: Optional[str] = None,
    new_price: Optional[float] = None,
    new_location: Optional[str] = None
) -> str:
    """
    批量修改符合条件的多节课程。

    参数说明:
    - title_pattern: 课程名称模糊匹配，如 "钢琴课"
    - student_name: 学生姓名，精确匹配
    - date_range: 日期范围，格式 "YYYY-MM-DD,YYYY-MM-DD"
    - weekday: 指定星期几，如 "周二"
    - new_time: 新时间，格式 "HH:MM,HH:MM" (开始,结束)
    - new_price: 新价格
    - new_location: 新地点

    示例:
    - "把所有周六的钢琴课都改到上午10点到11点"
      → title_pattern="钢琴课", weekday="周六", new_time="10:00,11:00"
    - "把张三3月份的课程价格改成200"
      → student_name="张三", date_range="2026-03-01,2026-03-31", new_price=200
    """
    try:
        stats = bulk_update_courses_filtered(
            title_pattern=title_pattern,
            student_name=student_name,
            date_range=date_range,
            weekday=weekday,
            new_time=new_time,
            new_price=new_price,
            new_location=new_location,
        )

        matched = int(stats.get("matched") or 0)
        updated = int(stats.get("updated") or 0)
        if matched == 0:
            return f"⚠️ 没有找到符合条件的课程"

        result = f"🔄 批量修改完成\n"
        result += f"━━━━━━━━━━━━━━━━━━━━━━\n"
        result += f"📋 匹配到: {matched} 节课\n"
        result += f"✅ 实际更新: {updated} 节课\n"
        if updated < matched:
            result += f"💡 提示：部分课程可能新值与旧值相同，因此数据库未计为“更新”。\n"
        return result

    except Exception as e:
        return f"⚠️ 批量修改时出错: {str(e)}"


@tool
def batch_remove_courses_tool(
    title_pattern: str = "",
    student_name: str = "",
    date_range: Optional[str] = None,
    weekday: Optional[str] = None
) -> str:
    """
    批量删除符合条件的多节课程。

    参数说明:
    - title_pattern: 课程名称模糊匹配
    - student_name: 学生姓名
    - date_range: 日期范围 "YYYY-MM-DD,YYYY-MM-DD"
    - weekday: 指定星期几

    示例:
    - "取消张三3月份的所有课程"
      → student_name="张三", date_range="2026-03-01,2026-03-31"
    - "删除所有周六的钢琴课"
      → title_pattern="钢琴课", weekday="周六"
    """
    try:
        stats = bulk_delete_courses_filtered(
            title_pattern=title_pattern,
            student_name=student_name,
            date_range=date_range,
            weekday=weekday,
        )

        matched = int(stats.get("matched") or 0)
        deleted = int(stats.get("deleted") or 0)
        if matched == 0:
            return f"⚠️ 没有找到符合条件的课程"

        result = f"🗑️ 批量删除完成\n"
        result += f"━━━━━━━━━━━━━━━━━━━━━━\n"
        result += f"📋 匹配到: {matched} 节课\n"
        result += f"✅ 实际删除: {deleted} 节课\n"
        return result

    except Exception as e:
        return f"⚠️ 批量删除时出错: {str(e)}"


@tool
def query_courses_tool(
    title_pattern: str = "",
    student_name: str = "",
    date_range: Optional[str] = None,
    weekday: Optional[str] = None
) -> str:
    """
    按条件查询课程列表（支持多种筛选组合）。

    参数说明:
    - title_pattern: 课程名称（模糊搜索），如 "钢琴"、"数学"
    - student_name: 学生姓名
    - date_range: 日期范围 "YYYY-MM-DD,YYYY-MM-DD"
    - weekday: 星期几 "周一"到"周日"

    示例:
    - "显示所有钢琴课" → title_pattern="钢琴课"
    - "显示4月份的课程" → date_range="2026-04-01,2026-04-30"
    - "周六有哪些课" → weekday="周六"
    - "张三的钢琴课" → title_pattern="钢琴", student_name="张三"
    """
    try:
        filtered = query_courses_filtered(
            title_pattern=title_pattern,
            student_name=student_name,
            date_range=date_range,
            weekday=weekday,
        )

        if not filtered:
            return f"📋 没有找到符合条件的课程"

        result = f"📋 查询结果 ({len(filtered)}节课)\n"
        result += f"━━━━━━━━━━━━━━━━━━━━━━\n\n"

        for c in filtered:
            s_name = c.student_name or "未知"
            wd = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][c.start.weekday()]

            result += f"📌 {c.title}\n"
            result += f"   📅 {c.start.strftime('%Y-%m-%d')} {wd} {c.start.strftime('%H:%M')}-{c.end.strftime('%H:%M')}\n"
            result += f"   👤 {s_name} | 💰 ¥{c.price}\n"
            if c.location:
                result += f"   📍 {c.location}\n"
            result += "\n"

        total_income = sum(c.price for c in filtered)
        result += f"💵 总收入: ¥{total_income:.0f}"

        return result

    except Exception as e:
        return f"⚠️ 查询课程时出错: {str(e)}"


# ==================== Notification Tools (NEW) ====================

@tool
def get_upcoming_lessons_tool(hours: int = 24) -> str:
    """获取未来 N 小时内的课程清单（用于每日提醒）"""
    now = datetime.now()
    end_time = now + timedelta(hours=hours)

    all_courses = get_all_courses()
    upcoming = [c for c in all_courses if now <= c.start <= end_time]
    upcoming.sort(key=lambda c: c.start)

    if not upcoming:
        return f"🔔 未来 {hours} 小时内暂无课程安排"

    result = f"🔔 未来 {hours} 小时内的课程\n"
    result += "━━━━━━━━━━━━━━━━━━━━━━\n"

    for c in upcoming:
        hours_until = (c.start - now).total_seconds() / 3600
        time_desc = f"{int(hours_until)}小时后" if hours_until >= 1 else f"{int(hours_until*60)}分钟后"
        result += f"⏰ {time_desc} - {c.title}\n"
        result += f"   📅 {c.start.strftime('%m-%d %H:%M')}-{c.end.strftime('%H:%M')}\n"
        result += f"   👤 {c.student_name or '未知'}\n\n"

    return result

@tool
def get_absent_students_tool(days: int = 30) -> str:
    """找出 N 天未上课的学生（跟进关怀）"""
    all_students = get_all_students()
    all_courses = get_all_courses()
    now = datetime.now()
    cutoff_date = now - timedelta(days=days)

    # 记录每个学生最后上课时间
    last_lesson_time = {}

    for c in all_courses:
        if c.student_id not in last_lesson_time or c.start > last_lesson_time[c.student_id]:
            last_lesson_time[c.student_id] = c.start

    # 找出长时间未上课的学生
    absent_students = []
    for student in all_students:
        if student.id not in last_lesson_time:
            # 从未上过课
            absent_students.append((student, None))
        elif last_lesson_time[student.id] < cutoff_date:
            days_since = (now - last_lesson_time[student.id]).days
            absent_students.append((student, days_since))

    if not absent_students:
        return f"✅ 所有学生在最近 {days} 天内都有上课记录"

    result = f"⚠️ 超过 {days} 天未上课的学生\n"
    result += "━━━━━━━━━━━━━━━━━━━━━━\n"

    for student, days_since in sorted(absent_students, key=lambda x: x[1] if x[1] else 999):
        if days_since is None:
            result += f"  • {student.name} - 从未上课记录\n"
        else:
            result += f"  • {student.name} - {days_since} 天前最后上课\n"
            if student.phone:
                result += f"    📱 {student.phone}\n"

    return result

@tool
def get_weekly_overview_tool() -> str:
    """获取本周课程概览（包括收入、学生数、每日分布）"""
    now = datetime.now()

    # 如果是周日(6)，则"本周"指向下一周（周一到周日）
    if now.weekday() == 6:
        week_start = now + timedelta(days=1)
    else:
        week_start = now - timedelta(days=now.weekday())

    week_start = week_start.replace(hour=0, minute=0, second=0, microsecond=0)
    week_end = week_start + timedelta(days=7)  # 到下周日 23:59:59

    all_courses = get_all_courses()
    week_courses = [c for c in all_courses if week_start <= c.start < week_end]

    if not week_courses:
        return f"📅 本周暂无课程安排"

    # 按日期统计
    daily_stats = {}
    weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

    for c in week_courses:
        date_key = c.start.date()
        if date_key not in daily_stats:
            daily_stats[date_key] = {"courses": [], "income": 0}
        daily_stats[date_key]["courses"].append(c)
        daily_stats[date_key]["income"] += c.price

    total_income = sum(c.price for c in week_courses)
    total_hours = sum((c.end - c.start).total_seconds() / 3600 for c in week_courses)
    unique_students = set(c.student_id for c in week_courses)

    result = f"""📅 本周课程概览 ({week_start.strftime('%Y-%m-%d')} - {(week_end - timedelta(days=1)).strftime('%Y-%m-%d')})
━━━━━━━━━━━━━━━━━━━━━━

📊 本周统计:
  • 总课时: {len(week_courses)} 节
  • 总时长: {total_hours:.1f} 小时
  • 学生数: {len(unique_students)} 人
  • 预计收入: ¥{total_income:.0f}

📋 每日安排:
"""

    for date in sorted(daily_stats.keys()):
        stats = daily_stats[date]
        weekday = weekday_names[date.weekday()]
        courses_count = len(stats["courses"])
        income = stats["income"]
        result += f"  • {date.strftime('%m-%d')} {weekday}: {courses_count}节课, ¥{income:.0f}\n"

    return result
