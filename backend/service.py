"""
数据库服务层 - 使用 MySQL 替代 JSON 文件存储
遵循 SOLID 原则：单一职责，所有数据访问集中在此模块
"""
import pymysql
from typing import List, Optional, Dict
from datetime import datetime
from contextlib import contextmanager
from .models import Course, CourseCreate, CourseUpdate, Student, StudentCreate, StudentUpdate

# ==================== 数据库配置 ====================

DB_CONFIG = {
    "host": "8.155.162.119",
    "port": 3306,
    "user": "root",
    "password": "xsy19507",
    "database": "course_scheduling",
    "charset": "utf8mb4",
    "autocommit": False
}


@contextmanager
def get_db_cursor():
    """
    数据库连接上下文管理器
    自动处理连接的获取和释放，确保资源安全
    """
    conn = pymysql.connect(**DB_CONFIG)
    try:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


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
