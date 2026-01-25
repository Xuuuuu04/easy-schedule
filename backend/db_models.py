from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime
import uuid

# ==================== SQLAlchemy Models ====================

class StudentModel(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(100), nullable=False, index=True)
    grade = Column(String(50), nullable=True)
    phone = Column(String(50), nullable=True)
    parent_contact = Column(String(100), nullable=True)
    progress = Column(Integer, default=0)
    notes = Column(Text, nullable=True)

    # 关系: 一个学生有多个课程
    courses = relationship("CourseModel", back_populates="student", cascade="all, delete-orphan")


class CourseModel(Base):
    __tablename__ = "courses"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(200), nullable=False, index=True)
    start = Column(DateTime, nullable=False, index=True)
    end = Column(DateTime, nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False, index=True)
    price = Column(Float, nullable=False, default=0.0)
    color = Column(String(20), default="#F5A3C8")
    description = Column(Text, nullable=True)
    location = Column(String(200), nullable=True)

    # 关系: 课程属于一个学生
    student = relationship("StudentModel", back_populates="courses")
