from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import uuid

# ==================== Student Models ====================

class StudentBase(BaseModel):
    name: str = Field(..., description="Student name")
    grade: Optional[str] = Field(None, description="Grade level")
    phone: Optional[str] = Field(None, description="Contact phone")
    parent_contact: Optional[str] = Field(None, description="Parent contact")
    progress: int = Field(0, ge=0, le=100, description="Learning progress (0-100)")
    notes: Optional[str] = Field(None, description="Additional notes")

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel):
    name: Optional[str] = None
    grade: Optional[str] = None
    phone: Optional[str] = None
    parent_contact: Optional[str] = None
    progress: Optional[int] = None
    notes: Optional[str] = None

class Student(StudentBase):
    id: int = Field(..., description="Student ID")

    class Config:
        json_encoders = {}


# ==================== Course Models ====================

class CourseBase(BaseModel):
    title: str = Field(..., description="Name of the course")
    start: datetime = Field(..., description="Start time of the course")
    end: datetime = Field(..., description="End time of the course")
    student_id: int = Field(..., description="Foreign key to Student")
    price: float = Field(..., ge=0, description="Price of the session")
    color: str = Field("#F5A3C8", description="Color code for the course card")
    description: Optional[str] = Field(None, description="Additional notes")
    location: Optional[str] = Field(None, description="Course location")

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    title: Optional[str] = None
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    student_id: Optional[int] = None
    price: Optional[float] = None
    color: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None

class Course(CourseBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Computed field - not stored in DB, added during serialization
    student_name: Optional[str] = None
    student_grade: Optional[str] = None

    class Config:
        json_encoders = {}
