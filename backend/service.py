"""
数据库服务层 - 使用 MySQL 替代 JSON 文件存储
遵循 SOLID 原则：单一职责，所有数据访问集中在此模块
"""
import pymysql
from typing import List, Optional, Dict
from datetime import datetime
from contextlib import contextmanager
from .models import Course, CourseCreate, CourseUpdate, Student, StudentCreate, StudentUpdate
from .config import settings
import uuid
from queue import LifoQueue, Empty

# ==================== 数据库配置 ====================

DB_CONFIG = {
    "host": settings.DB_HOST,
    "port": settings.DB_PORT,
    "user": settings.DB_USER,
    "password": settings.DB_PASSWORD,
    "database": settings.DB_NAME,
    "charset": "utf8mb4",
    "autocommit": False
}

_POOL_SIZE = max(1, int(getattr(settings, "DB_POOL_SIZE", 5)))
_CONN_POOL: LifoQueue = LifoQueue(maxsize=_POOL_SIZE)


def _acquire_conn():
    try:
        conn = _CONN_POOL.get_nowait()
    except Empty:
        conn = pymysql.connect(**DB_CONFIG)

    try:
        conn.ping(reconnect=True)
    except Exception:
        try:
            conn.close()
        except Exception:
            pass
        conn = pymysql.connect(**DB_CONFIG)

    return conn


def _release_conn(conn, healthy: bool):
    if not healthy:
        try:
            conn.close()
        except Exception:
            pass
        return
    try:
        _CONN_POOL.put_nowait(conn)
    except Exception:
        try:
            conn.close()
        except Exception:
            pass


@contextmanager
def get_db_cursor():
    """
    数据库连接上下文管理器
    自动处理连接的获取和释放，确保资源安全
    """
    conn = _acquire_conn()
    healthy = True
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        yield cursor
        conn.commit()
    except Exception:
        try:
            conn.rollback()
        except Exception:
            healthy = False
        raise
    finally:
        try:
            cursor.close()
        except Exception:
            pass
        _release_conn(conn, healthy=healthy)


# ==================== 学生服务 ====================

def get_all_students() -> List[Student]:
    """获取所有学生"""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM students ORDER BY id")
        return [Student(**row) for row in cursor.fetchall()]


def get_student(student_id: int) -> Optional[Student]:
    """根据 ID 获取学生"""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM students WHERE id = %s", (student_id,))
        row = cursor.fetchone()
        return Student(**row) if row else None


def get_student_by_name(name: str) -> Optional[Student]:
    """根据姓名获取学生"""
    with get_db_cursor() as cursor:
        cursor.execute("SELECT * FROM students WHERE name = %s", (name,))
        row = cursor.fetchone()
        return Student(**row) if row else None


def create_student(student_in: StudentCreate) -> Student:
    """创建新学生，ID 由数据库自增生成"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            INSERT INTO students (name, grade, phone, parent_contact, progress, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            student_in.name,
            student_in.grade,
            student_in.phone,
            student_in.parent_contact,
            student_in.progress if student_in.progress is not None else 0,
            student_in.notes
        ))
        new_id = cursor.lastrowid
        # 获取完整记录
        cursor.execute("SELECT * FROM students WHERE id = %s", (new_id,))
        return Student(**cursor.fetchone())


def update_student(student_id: int, student_in: StudentUpdate) -> Optional[Student]:
    """更新学生信息"""
    with get_db_cursor() as cursor:
        # 构建动态 UPDATE 语句
        update_data = student_in.dict(exclude_unset=True)
        if not update_data:
            return get_student(student_id)

        set_clause = ", ".join(f"{k} = %s" for k in update_data.keys())
        values = list(update_data.values()) + [student_id]

        cursor.execute(
            f"UPDATE students SET {set_clause} WHERE id = %s",
            values
        )

        if cursor.rowcount > 0:
            return get_student(student_id)
        return None


def delete_student(student_id: int) -> bool:
    """
    删除学生
    级联删除由数据库外键约束自动处理
    """
    with get_db_cursor() as cursor:
        cursor.execute("DELETE FROM students WHERE id = %s", (student_id,))
        return cursor.rowcount > 0


# ==================== 课程服务 ====================

def _enrich_course_with_student(course_data: dict) -> dict:
    """
    为课程数据填充学生信息（计算字段）
    DRY 原则：统一处理学生信息填充
    """
    student = get_student(course_data['student_id'])
    if student:
        course_data['student_name'] = student.name
        course_data['student_grade'] = student.grade
    else:
        course_data['student_name'] = "未知学生"
        course_data['student_grade'] = ""
    return course_data


def get_all_courses() -> List[Course]:
    """
    获取所有课程，带学生信息
    数据库通过 JOIN 一次查询完成，比 JSON 方式更高效
    """
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT c.*,
                   s.name as student_name,
                   s.grade as student_grade
            FROM courses c
            LEFT JOIN students s ON c.student_id = s.id
            ORDER BY c.start
        """)
        return [Course(**row) for row in cursor.fetchall()]


def get_course(course_id: str) -> Optional[Course]:
    """根据 UUID 获取单个课程"""
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT c.*,
                   s.name as student_name,
                   s.grade as student_grade
            FROM courses c
            LEFT JOIN students s ON c.student_id = s.id
            WHERE c.id = %s
        """, (course_id,))
        row = cursor.fetchone()
        return Course(**row) if row else None


def create_course(course_in: CourseCreate) -> Course:
    """
    创建新课程
    学生存在性由数据库外键约束保证
    """
    import uuid

    with get_db_cursor() as cursor:
        course_id = str(uuid.uuid4())

        # 验证学生存在 - 直接查询，不需要额外函数调用
        cursor.execute("SELECT * FROM students WHERE id = %s", (course_in.student_id,))
        student_row = cursor.fetchone()
        if not student_row:
            raise ValueError(f"Student with id {course_in.student_id} not found")

        # 插入课程
        cursor.execute("""
            INSERT INTO courses (id, title, start, end, student_id, price, color, description, location)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            course_id,
            course_in.title,
            course_in.start,
            course_in.end,
            course_in.student_id,
            course_in.price,
            course_in.color if course_in.color else "#F5A3C8",
            course_in.description,
            course_in.location
        ))

        # 在同一个事务中查询刚插入的数据
        cursor.execute("""
            SELECT c.*,
                   s.name as student_name,
                   s.grade as student_grade
            FROM courses c
            LEFT JOIN students s ON c.student_id = s.id
            WHERE c.id = %s
        """, (course_id,))
        row = cursor.fetchone()
        return Course(**row)


def update_course(course_id: str, course_in: CourseUpdate) -> Optional[Course]:
    """
    更新课程
    如果修改 student_id，数据库外键约束会自动验证
    """
    with get_db_cursor() as cursor:
        update_data = course_in.dict(exclude_unset=True)
        if not update_data:
            return get_course(course_id)

        # 如果要修改学生，先验证
        if 'student_id' in update_data:
            student = get_student(update_data['student_id'])
            if not student:
                raise ValueError(f"Student with id {update_data['student_id']} not found")

        set_clause = ", ".join(f"{k} = %s" for k in update_data.keys())
        values = list(update_data.values()) + [course_id]

        cursor.execute(
            f"UPDATE courses SET {set_clause} WHERE id = %s",
            values
        )

        if cursor.rowcount > 0:
            return get_course(course_id)
        return None


def delete_course(course_id: str) -> bool:
    """删除课程"""
    with get_db_cursor() as cursor:
        cursor.execute("DELETE FROM courses WHERE id = %s", (course_id,))
        return cursor.rowcount > 0


def check_conflicts(start: datetime, end: datetime, exclude_id: str = None) -> List[Course]:
    """
    检测时间冲突
    使用数据库原生的时间比较，比 Python 循环更高效
    """
    with get_db_cursor() as cursor:
        if exclude_id:
            cursor.execute("""
                SELECT c.*,
                       s.name as student_name,
                       s.grade as student_grade
                FROM courses c
                LEFT JOIN students s ON c.student_id = s.id
                WHERE c.id != %s
                  AND c.start < %s
                  AND c.end > %s
                ORDER BY c.start
            """, (exclude_id, end, start))
        else:
            cursor.execute("""
                SELECT c.*,
                       s.name as student_name,
                       s.grade as student_grade
                FROM courses c
                LEFT JOIN students s ON c.student_id = s.id
                WHERE c.start < %s
                  AND c.end > %s
                ORDER BY c.start
            """, (end, start))

        return [Course(**row) for row in cursor.fetchall()]


def _parse_date_range(date_range: Optional[str]) -> Optional[tuple[str, str]]:
    if not date_range:
        return None
    try:
        start_str, end_str = date_range.split(",")
        start_date = datetime.fromisoformat(start_str.strip()).date().isoformat()
        end_date = datetime.fromisoformat(end_str.strip()).date().isoformat()
        return start_date, end_date
    except Exception as e:
        raise ValueError("日期范围格式错误，请使用: YYYY-MM-DD,YYYY-MM-DD") from e


def _weekday_to_mysql(weekday: Optional[str]) -> Optional[int]:
    if not weekday:
        return None
    weekday_map = {"周一": 0, "周二": 1, "周三": 2, "周四": 3, "周五": 4, "周六": 5, "周日": 6}
    if weekday not in weekday_map:
        raise ValueError("星期格式错误，请使用: 周一/周二/.../周日")
    return weekday_map[weekday]


def _build_course_where_clause(
    title_pattern: str = "",
    student_name: str = "",
    date_range: Optional[str] = None,
    weekday: Optional[str] = None,
    course_alias: str = "c",
    student_alias: str = "s",
) -> tuple[str, list]:
    clauses = ["1=1"]
    params: list = []

    if title_pattern:
        clauses.append(f"{course_alias}.title LIKE %s")
        params.append(f"%{title_pattern}%")

    if student_name:
        clauses.append(f"{student_alias}.name = %s")
        params.append(student_name)

    parsed_range = _parse_date_range(date_range)
    if parsed_range:
        start_date, end_date = parsed_range
        clauses.append(f"DATE({course_alias}.start) BETWEEN %s AND %s")
        params.extend([start_date, end_date])

    mysql_wd = _weekday_to_mysql(weekday)
    if mysql_wd is not None:
        clauses.append(f"WEEKDAY({course_alias}.start) = %s")
        params.append(mysql_wd)

    return " AND ".join(clauses), params


def query_courses_filtered(
    title_pattern: str = "",
    student_name: str = "",
    date_range: Optional[str] = None,
    weekday: Optional[str] = None,
    limit: Optional[int] = None,
) -> List[Course]:
    where_clause, params = _build_course_where_clause(
        title_pattern=title_pattern,
        student_name=student_name,
        date_range=date_range,
        weekday=weekday,
        course_alias="c",
        student_alias="s",
    )

    sql = f"""
        SELECT c.*,
               s.name as student_name,
               s.grade as student_grade
        FROM courses c
        LEFT JOIN students s ON c.student_id = s.id
        WHERE {where_clause}
        ORDER BY c.start
    """
    if limit is not None:
        sql += " LIMIT %s"
        params.append(int(limit))

    with get_db_cursor() as cursor:
        cursor.execute(sql, params)
        return [Course(**row) for row in cursor.fetchall()]


def count_courses_filtered(
    title_pattern: str = "",
    student_name: str = "",
    date_range: Optional[str] = None,
    weekday: Optional[str] = None,
) -> int:
    where_clause, params = _build_course_where_clause(
        title_pattern=title_pattern,
        student_name=student_name,
        date_range=date_range,
        weekday=weekday,
        course_alias="c",
        student_alias="s",
    )
    with get_db_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT COUNT(*) as cnt
            FROM courses c
            LEFT JOIN students s ON c.student_id = s.id
            WHERE {where_clause}
            """,
            params,
        )
        row = cursor.fetchone()
        return int(row["cnt"]) if row and row.get("cnt") is not None else 0


def bulk_update_courses_filtered(
    title_pattern: str = "",
    student_name: str = "",
    date_range: Optional[str] = None,
    weekday: Optional[str] = None,
    new_time: Optional[str] = None,
    new_price: Optional[float] = None,
    new_location: Optional[str] = None,
) -> dict:
    where_clause, params = _build_course_where_clause(
        title_pattern=title_pattern,
        student_name=student_name,
        date_range=date_range,
        weekday=weekday,
        course_alias="c",
        student_alias="s",
    )

    set_clauses = []
    set_params: list = []

    if new_time:
        try:
            start_str, end_str = [x.strip() for x in new_time.split(",")]
            if len(start_str.split(":")) == 2:
                start_str = f"{start_str}:00"
            if len(end_str.split(":")) == 2:
                end_str = f"{end_str}:00"
        except Exception as e:
            raise ValueError("new_time 格式错误，请使用: HH:MM,HH:MM") from e

        set_clauses.append("c.start = TIMESTAMP(DATE(c.start), %s)")
        set_params.append(start_str)
        set_clauses.append("c.end = TIMESTAMP(DATE(c.end), %s)")
        set_params.append(end_str)

    if new_price is not None:
        set_clauses.append("c.price = %s")
        set_params.append(float(new_price))

    if new_location is not None:
        set_clauses.append("c.location = %s")
        set_params.append(new_location)

    if not set_clauses:
        return {"matched": 0, "updated": 0}

    with get_db_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT COUNT(*) as cnt
            FROM courses c
            LEFT JOIN students s ON c.student_id = s.id
            WHERE {where_clause}
            """,
            params,
        )
        matched = int(cursor.fetchone()["cnt"])
        if matched == 0:
            return {"matched": 0, "updated": 0}

        cursor.execute(
            f"""
            UPDATE courses c
            LEFT JOIN students s ON c.student_id = s.id
            SET {", ".join(set_clauses)}
            WHERE {where_clause}
            """,
            set_params + params,
        )
        return {"matched": matched, "updated": int(cursor.rowcount)}


def bulk_delete_courses_filtered(
    title_pattern: str = "",
    student_name: str = "",
    date_range: Optional[str] = None,
    weekday: Optional[str] = None,
) -> dict:
    where_clause, params = _build_course_where_clause(
        title_pattern=title_pattern,
        student_name=student_name,
        date_range=date_range,
        weekday=weekday,
        course_alias="c",
        student_alias="s",
    )

    with get_db_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT COUNT(*) as cnt
            FROM courses c
            LEFT JOIN students s ON c.student_id = s.id
            WHERE {where_clause}
            """,
            params,
        )
        matched = int(cursor.fetchone()["cnt"])
        if matched == 0:
            return {"matched": 0, "deleted": 0}

        cursor.execute(
            f"""
            DELETE c
            FROM courses c
            LEFT JOIN students s ON c.student_id = s.id
            WHERE {where_clause}
            """,
            params,
        )
        return {"matched": matched, "deleted": int(cursor.rowcount)}


def bulk_create_recurring_courses(
    title: str,
    student_name: str,
    start_date: str,
    end_date: str,
    weekdays: str,
    start_time: str,
    end_time: str,
    price: float,
    grade: str = "",
    description: str = "",
    location: Optional[str] = None,
    color: str = "#F5A3C8",
) -> dict:
    try:
        start = datetime.fromisoformat(start_date).date()
        end = datetime.fromisoformat(end_date).date()
    except Exception as e:
        raise ValueError("日期格式错误，请使用 YYYY-MM-DD") from e

    def parse_hhmm(value: str):
        value = value.strip()
        try:
            return datetime.strptime(value, "%H:%M").time()
        except ValueError:
            return datetime.fromisoformat(value).time()

    time_start = parse_hhmm(start_time)
    time_end = parse_hhmm(end_time)
    if datetime.combine(datetime.today().date(), time_end) <= datetime.combine(datetime.today().date(), time_start):
        raise ValueError("结束时间必须晚于开始时间")

    weekday_map = {
        "周一": 0,
        "周二": 1,
        "周三": 2,
        "周四": 3,
        "周五": 4,
        "周六": 5,
        "周日": 6,
        "0": 0,
        "1": 1,
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "monday": 0,
        "tuesday": 1,
        "wednesday": 2,
        "thursday": 3,
        "friday": 4,
        "saturday": 5,
        "sunday": 6,
    }

    target_weekdays: set[int] = set()
    for w in weekdays.split(","):
        key = w.strip().lower()
        if key in weekday_map:
            target_weekdays.add(weekday_map[key])

    if not target_weekdays:
        raise ValueError("星期格式错误，请使用：周一/周二/... 或 0/1/.../6")

    if end < start:
        raise ValueError("结束日期必须不早于开始日期")

    course_dates = []
    cur = start
    while cur <= end:
        if cur.weekday() in target_weekdays:
            course_dates.append(cur)
        cur = cur.fromordinal(cur.toordinal() + 1)

    if not course_dates:
        return {"auto_created": False, "created": 0, "conflicts": [], "months": {}, "expected_income": 0.0}

    min_start_dt = datetime.combine(course_dates[0], time_start)
    max_end_dt = datetime.combine(course_dates[-1], time_end)

    with get_db_cursor() as cursor:
        cursor.execute("SELECT id, grade FROM students WHERE name = %s", (student_name,))
        student_row = cursor.fetchone()
        auto_created = False
        if not student_row:
            cursor.execute(
                """
                INSERT INTO students (name, grade, phone, parent_contact, progress, notes)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (student_name, grade if grade else None, None, None, 0, None),
            )
            student_id = cursor.lastrowid
            student_grade = grade if grade else None
            auto_created = True
        else:
            student_id = student_row["id"]
            student_grade = student_row.get("grade")

        cursor.execute(
            """
            SELECT start, end
            FROM courses
            WHERE start < %s AND end > %s
            """,
            (max_end_dt, min_start_dt),
        )
        existing = cursor.fetchall() or []

        by_date: dict[str, list[tuple[datetime, datetime]]] = {}
        for row in existing:
            s = row["start"]
            e = row["end"]
            if not s or not e:
                continue
            key = s.date().isoformat()
            by_date.setdefault(key, []).append((s, e))

        to_insert = []
        conflicts = []
        for d in course_dates:
            course_start = datetime.combine(d, time_start)
            course_end = datetime.combine(d, time_end)
            conflict_intervals = by_date.get(d.isoformat(), [])
            has_conflict = False
            for s, e in conflict_intervals:
                if course_start < e and course_end > s:
                    has_conflict = True
                    break
            if has_conflict:
                conflicts.append(d.isoformat())
                continue

            cid = str(uuid.uuid4())
            to_insert.append(
                (
                    cid,
                    title,
                    course_start,
                    course_end,
                    student_id,
                    float(price),
                    color if color else "#F5A3C8",
                    description,
                    location,
                )
            )

        if to_insert:
            cursor.executemany(
                """
                INSERT INTO courses (id, title, start, end, student_id, price, color, description, location)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                to_insert,
            )

        months: dict[str, int] = {}
        for row in to_insert:
            month_key = row[2].strftime("%Y-%m")
            months[month_key] = months.get(month_key, 0) + 1

        expected_income = sum(row[5] for row in to_insert)

        return {
            "auto_created": auto_created,
            "student_grade": student_grade,
            "created": len(to_insert),
            "conflicts": conflicts,
            "months": months,
            "expected_income": expected_income,
        }


# ==================== 财务统计 ====================

def get_financial_report() -> Dict:
    """
    财务收入统计
    利用数据库聚合函数，高效计算
    """
    with get_db_cursor() as cursor:
        cursor.execute("""
            SELECT
                COUNT(*) as total_courses,
                COALESCE(SUM(price), 0) as total_income,
                COALESCE(AVG(price), 0) as avg_price
            FROM courses
        """)
        stats = cursor.fetchone()

        cursor.execute("""
            SELECT s.name, s.id, COUNT(c.id) as course_count, SUM(c.price) as total
            FROM students s
            LEFT JOIN courses c ON s.id = c.student_id
            GROUP BY s.id, s.name
            ORDER BY total DESC
        """)
        by_student = cursor.fetchall()

        return {
            "total_courses": stats['total_courses'],
            "total_income": float(stats['total_income']),
            "avg_price": float(stats['avg_price']),
            "by_student": by_student
        }
