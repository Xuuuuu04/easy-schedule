import json
import os
from typing import List, Optional, Dict
from datetime import datetime
from .models import Course, CourseCreate, CourseUpdate, Student, StudentCreate, StudentUpdate

DATA_FILE = "data/courses.json"
STUDENTS_FILE = "data/students.json"

# Sample student data for initialization
SAMPLE_STUDENTS = [
    {
        "id": 1,
        "name": "林小雪",
        "grade": "小学三年级",
        "phone": "138****1234",
        "parent_contact": "林妈妈 139****5678",
        "progress": 75,
        "notes": "钢琴启蒙阶段，练习自觉，需要多鼓励指法练习"
    },
    {
        "id": 2,
        "name": "王浩宇",
        "grade": "小学四年级",
        "phone": "137****2345",
        "parent_contact": "王爸爸 136****9012",
        "progress": 45,
        "notes": "活泼好动，对乐理感兴趣，但坐不住需要分段练习"
    },
    {
        "id": 3,
        "name": "陈思涵",
        "grade": "初中一年级",
        "phone": "159****3456",
        "parent_contact": "陈妈妈 158****7890",
        "progress": 90,
        "notes": "学琴五年，基础扎实，正在准备考级，专注力很好"
    },
    {
        "id": 4,
        "name": "张艺萌",
        "grade": "幼儿园大班",
        "phone": "186****4567",
        "parent_contact": "张奶奶 185****1234",
        "notes": "刚起步，手型需要纠正，建议每次上课30分钟"
    },
    {
        "id": 5,
        "name": "刘子轩",
        "grade": "小学二年级",
        "phone": "135****6789",
        "parent_contact": "刘妈妈 134****4567",
        "progress": 60,
        "notes": "节奏感好，但读谱需要加强，家长配合度很高"
    }
]

def _ensure_data_dir():
    if not os.path.exists("data"):
        os.makedirs("data")
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
    if not os.path.exists(STUDENTS_FILE):
        # Initialize with sample students
        with open(STUDENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(SAMPLE_STUDENTS, f, indent=2, ensure_ascii=False)

def _read_data() -> List[dict]:
    _ensure_data_dir()
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _write_data(data: List[dict]):
    _ensure_data_dir()
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)

def _read_students() -> List[dict]:
    _ensure_data_dir()
    try:
        with open(STUDENTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []

def _write_students(data: List[dict]):
    _ensure_data_dir()
    with open(STUDENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

# Student lookup cache
_students_cache: Dict[int, Student] = {}

def _refresh_students_cache():
    global _students_cache
    _students_cache = {}
    for s in get_all_students():
        _students_cache[s.id] = s

def get_student_by_id_cached(student_id: int) -> Optional[Student]:
    if not _students_cache:
        _refresh_students_cache()
    return _students_cache.get(student_id)

# ==================== Course Services ====================

def get_all_courses() -> List[Course]:
    data = _read_data()
    courses = []
    for item in data:
        course = Course(**item)
        # Add student info as computed fields
        student = get_student_by_id_cached(course.student_id)
        if student:
            course.student_name = student.name
            course.student_grade = student.grade
        courses.append(course)
    return courses

def get_course(course_id: str) -> Optional[Course]:
    courses = get_all_courses()
    for course in courses:
        if course.id == course_id:
            return course
    return None

def create_course(course_in: CourseCreate) -> Course:
    courses_data = _read_data()

    # Validate student exists
    student = get_student_by_id_cached(course_in.student_id)
    if not student:
        raise ValueError(f"Student with id {course_in.student_id} not found")

    # Conflict check
    for c_data in courses_data:
        c_start = datetime.fromisoformat(c_data['start'])
        c_end = datetime.fromisoformat(c_data['end'])
        if (course_in.start < c_end) and (course_in.end > c_start):
             pass  # Allow but could warn

    new_course = Course(**course_in.dict())
    # Add student name for immediate response
    new_course.student_name = student.name
    new_course.student_grade = student.grade

    courses_data.append(new_course.dict())
    _write_data(courses_data)
    return new_course

def update_course(course_id: str, course_in: CourseUpdate) -> Optional[Course]:
    courses_data = _read_data()
    for i, item in enumerate(courses_data):
        if item['id'] == course_id:
            updated_data = item.copy()
            update_data = course_in.dict(exclude_unset=True)

            # Validate student_id if being updated
            if 'student_id' in update_data:
                student = get_student_by_id_cached(update_data['student_id'])
                if not student:
                    raise ValueError(f"Student with id {update_data['student_id']} not found")

            for field in update_data:
                updated_data[field] = update_data[field]

            updated_course = Course(**updated_data)
            # Add student info
            student = get_student_by_id_cached(updated_course.student_id)
            if student:
                updated_course.student_name = student.name
                updated_course.student_grade = student.grade

            courses_data[i] = updated_course.dict()
            _write_data(courses_data)
            return updated_course
    return None

def delete_course(course_id: str) -> bool:
    courses_data = _read_data()
    initial_len = len(courses_data)
    courses_data = [c for c in courses_data if c['id'] != course_id]
    if len(courses_data) < initial_len:
        _write_data(courses_data)
        return True
    return False

def check_conflicts(start: datetime, end: datetime, exclude_id: str = None) -> List[Course]:
    courses = get_all_courses()
    conflicts = []
    for c in courses:
        if exclude_id and c.id == exclude_id:
            continue
        if (start < c.end) and (end > c.start):
            conflicts.append(c)
    return conflicts

# ==================== Student Services ====================

def get_all_students() -> List[Student]:
    data = _read_students()
    students = []
    for item in data:
        students.append(Student(**item))
    # Update cache without causing recursion
    global _students_cache
    for student in students:
        _students_cache[student.id] = student
    return students

def get_student(student_id: int) -> Optional[Student]:
    students = get_all_students()
    for student in students:
        if student.id == student_id:
            return student
    return None

def get_student_by_name(name: str) -> Optional[Student]:
    students = get_all_students()
    for student in students:
        if student.name == name:
            return student
    return None

def create_student(student_in: StudentCreate) -> Student:
    students = get_all_students()

    # Generate new ID (max existing + 1, or 1 if empty)
    if students:
        new_id = max(s.id for s in students) + 1
    else:
        new_id = 1

    new_student = Student(
        id=new_id,
        **student_in.dict()
    )
    students.append(new_student)
    _write_students([s.dict() for s in students])
    _refresh_students_cache()
    return new_student

def update_student(student_id: int, student_in: StudentUpdate) -> Optional[Student]:
    students = get_all_students()
    for i, student in enumerate(students):
        if student.id == student_id:
            updated_data = student.dict()
            # Remove id from updated_data to avoid duplicate
            updated_data.pop('id', None)
            update_data = student_in.dict(exclude_unset=True)
            for field in update_data:
                updated_data[field] = update_data[field]

            updated_student = Student(id=student_id, **updated_data)
            students[i] = updated_student
            _write_students([s.dict() for s in students])
            _refresh_students_cache()
            return updated_student
    return None

def delete_student(student_id: int) -> bool:
    """Delete a student and all their associated courses"""
    students = get_all_students()
    initial_len = len(students)

    # Get student info before deletion
    student_name = None
    for student in students:
        if student.id == student_id:
            student_name = student.name
            break

    # Delete student
    students = [s for s in students if s.id != student_id]
    if len(students) < initial_len:
        _write_students([s.dict() for s in students])
        _refresh_students_cache()

        # Delete all courses associated with this student
        courses_data = _read_data()
        courses_data = [c for c in courses_data if c.get('student_id') != student_id]
        _write_data(courses_data)

        return True
    return False
