"""
数据库服务层 - 使用 SQLAlchemy ORM
遵循 SOLID 原则：单一职责，所有数据访问集中在此模块
"""
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from .models import Course, CourseCreate, CourseUpdate, Student, StudentCreate, StudentUpdate
from .db_models import StudentModel, CourseModel
from .database import SessionLocal

# ==================== 辅助函数 ====================

def get_db_session():
    """获取数据库会话 (用于非 FastAPI 依赖场景，如 Tools)"""
    return SessionLocal()

# ==================== 学生服务 ====================

def get_all_students(limit: int = 100, offset: int = 0, name_filter: Optional[str] = None) -> List[Student]:
    """获取所有学生 (支持分页和筛选)"""
    with get_db_session() as db:
        query = db.query(StudentModel)
        
        if name_filter:
            query = query.filter(StudentModel.name.contains(name_filter))
            
        students = query.order_by(StudentModel.id).offset(offset).limit(limit).all()
        return [Student(**s.__dict__) for s in students]


def get_student(student_id: int) -> Optional[Student]:
    """根据 ID 获取学生"""
    with get_db_session() as db:
        student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
        return Student(**student.__dict__) if student else None


def get_student_by_name(name: str) -> Optional[Student]:
    """根据姓名获取学生"""
    with get_db_session() as db:
        student = db.query(StudentModel).filter(StudentModel.name == name).first()
        return Student(**student.__dict__) if student else None


def create_student(student_in: StudentCreate) -> Student:
    """创建新学生"""
    with get_db_session() as db:
        db_student = StudentModel(
            name=student_in.name,
            grade=student_in.grade,
            phone=student_in.phone,
            parent_contact=student_in.parent_contact,
            progress=student_in.progress,
            notes=student_in.notes
        )
        db.add(db_student)
        db.commit()
        db.refresh(db_student)
        return Student(**db_student.__dict__)


def update_student(student_id: int, student_in: StudentUpdate) -> Optional[Student]:
    """更新学生信息"""
    with get_db_session() as db:
        db_student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
        if not db_student:
            return None
        
        update_data = student_in.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_student, key, value)
        
        db.commit()
        db.refresh(db_student)
        return Student(**db_student.__dict__)


def delete_student(student_id: int) -> bool:
    """删除学生 (级联删除由 SQLAlchemy 模型关系处理)"""
    with get_db_session() as db:
        db_student = db.query(StudentModel).filter(StudentModel.id == student_id).first()
        if not db_student:
            return False
        
        db.delete(db_student)
        db.commit()
        return True


# ==================== 课程服务 ====================

def get_all_courses(limit: int = 100, offset: int = 0, start_date: Optional[str] = None, end_date: Optional[str] = None) -> List[Course]:
    """获取所有课程 (支持分页和日期筛选)"""
    with get_db_session() as db:
        query = db.query(CourseModel)
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date)
                query = query.filter(CourseModel.start >= start_dt)
            except ValueError:
                pass # Ignore invalid date format
                
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date)
                query = query.filter(CourseModel.end <= end_dt)
            except ValueError:
                pass

        courses = query.order_by(CourseModel.start).offset(offset).limit(limit).all()
        
        # 转换为 Pydantic 模型，手动填充学生信息
        result = []
        for c in courses:
            c_dict = c.__dict__.copy()
            if c.student:
                c_dict['student_name'] = c.student.name
                c_dict['student_grade'] = c.student.grade
            else:
                c_dict['student_name'] = "未知学生"
                c_dict['student_grade'] = ""
            result.append(Course(**c_dict))
            
        return result


def get_course(course_id: str) -> Optional[Course]:
    """根据 UUID 获取单个课程"""
    with get_db_session() as db:
        course = db.query(CourseModel).filter(CourseModel.id == course_id).first()
        if not course:
            return None
            
        c_dict = course.__dict__.copy()
        if course.student:
            c_dict['student_name'] = course.student.name
            c_dict['student_grade'] = course.student.grade
        else:
            c_dict['student_name'] = "未知学生"
            c_dict['student_grade'] = ""
            
        return Course(**c_dict)


def create_course(course_in: CourseCreate) -> Course:
    """创建新课程"""
    with get_db_session() as db:
        # 验证学生是否存在
        student = db.query(StudentModel).filter(StudentModel.id == course_in.student_id).first()
        if not student:
            raise ValueError(f"Student with id {course_in.student_id} not found")

        db_course = CourseModel(
            title=course_in.title,
            start=course_in.start,
            end=course_in.end,
            student_id=course_in.student_id,
            price=course_in.price,
            color=course_in.color or "#F5A3C8",
            description=course_in.description,
            location=course_in.location
        )
        db.add(db_course)
        db.commit()
        db.refresh(db_course)
        
        # 返回带学生信息的完整对象
        c_dict = db_course.__dict__.copy()
        c_dict['student_name'] = student.name
        c_dict['student_grade'] = student.grade
        return Course(**c_dict)


def update_course(course_id: str, course_in: CourseUpdate) -> Optional[Course]:
    """更新课程"""
    with get_db_session() as db:
        db_course = db.query(CourseModel).filter(CourseModel.id == course_id).first()
        if not db_course:
            return None
        
        update_data = course_in.dict(exclude_unset=True)
        
        # 如果更新学生，验证是否存在
        if 'student_id' in update_data:
            student = db.query(StudentModel).filter(StudentModel.id == update_data['student_id']).first()
            if not student:
                raise ValueError(f"Student with id {update_data['student_id']} not found")
        
        for key, value in update_data.items():
            setattr(db_course, key, value)
            
        db.commit()
        db.refresh(db_course)
        
        # 重新获取完整信息（包括可能更新的学生）
        return get_course(course_id)


def delete_course(course_id: str) -> bool:
    """删除课程"""
    with get_db_session() as db:
        db_course = db.query(CourseModel).filter(CourseModel.id == course_id).first()
        if not db_course:
            return False
            
        db.delete(db_course)
        db.commit()
        return True


def check_conflicts(start: datetime, end: datetime, exclude_id: str = None) -> List[Course]:
    """
    检测时间冲突 (下沉到数据库查询)
    Conflict condition: (NewStart < ExistingEnd) AND (NewEnd > ExistingStart)
    """
    with get_db_session() as db:
        query = db.query(CourseModel).filter(
            CourseModel.start < end,
            CourseModel.end > start
        )
        
        if exclude_id:
            query = query.filter(CourseModel.id != exclude_id)
            
        conflicts = query.order_by(CourseModel.start).all()
        
        # 转换为 Pydantic 模型
        result = []
        for c in conflicts:
            c_dict = c.__dict__.copy()
            # 简单填充，冲突检测可能不需要完整的学生详情，但保持一致性
            if c.student:
                c_dict['student_name'] = c.student.name
                c_dict['student_grade'] = c.student.grade
            else:
                c_dict['student_name'] = "未知"
                c_dict['student_grade'] = ""
            result.append(Course(**c_dict))
            
        return result


# ==================== 财务统计 ====================

def get_financial_report() -> Dict:
    """财务收入统计"""
    with get_db_session() as db:
        # 总体统计
        total_stats = db.query(
            func.count(CourseModel.id).label('count'),
            func.sum(CourseModel.price).label('income'),
            func.avg(CourseModel.price).label('avg')
        ).first()
        
        # 按学生统计
        student_stats = db.query(
            StudentModel.name,
            StudentModel.id,
            func.count(CourseModel.id).label('course_count'),
            func.sum(CourseModel.price).label('total')
        ).join(CourseModel, StudentModel.id == CourseModel.student_id)\
         .group_by(StudentModel.id, StudentModel.name)\
         .order_by(func.sum(CourseModel.price).desc()).all()
        
        return {
            "total_courses": total_stats.count or 0,
            "total_income": float(total_stats.income or 0),
            "avg_price": float(total_stats.avg or 0),
            "by_student": [
                {
                    "name": s.name,
                    "id": s.id,
                    "course_count": s.course_count,
                    "total": float(s.total or 0)
                }
                for s in student_stats
            ]
        }
