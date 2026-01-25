from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
import uuid

# ==================== Student Models ====================

class StudentBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Student name")
    grade: Optional[str] = Field(None, max_length=50, description="Grade level")
    phone: Optional[str] = Field(None, max_length=50, description="Contact phone")
    parent_contact: Optional[str] = Field(None, max_length=100, description="Parent contact")
    progress: int = Field(0, ge=0, le=100, description="Learning progress (0-100)")
    notes: Optional[str] = Field(None, max_length=500, description="Additional notes")

class StudentCreate(StudentBase):
    pass

class StudentUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    grade: Optional[str] = Field(None, max_length=50)
    phone: Optional[str] = Field(None, max_length=50)
    parent_contact: Optional[str] = Field(None, max_length=100)
    progress: Optional[int] = Field(None, ge=0, le=100)
    notes: Optional[str] = Field(None, max_length=500)

class Student(StudentBase):
    id: int = Field(..., description="Student ID")

    class Config:
        json_encoders = {}


# ==================== Course Models ====================

class CourseBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200, description="Name of the course")
    start: datetime = Field(..., description="Start time of the course")
    end: datetime = Field(..., description="End time of the course")
    student_id: int = Field(..., description="Foreign key to Student")
    price: float = Field(..., ge=0, description="Price of the session")
    color: str = Field("#F5A3C8", max_length=20, description="Color code for the course card")
    description: Optional[str] = Field(None, max_length=500, description="Additional notes")
    location: Optional[str] = Field(None, max_length=200, description="Course location")

    @validator("end")
    def end_must_be_after_start(cls, v, values):
        if "start" in values and v <= values["start"]:
            raise ValueError("End time must be after start time")
        return v

class CourseCreate(CourseBase):
    pass

class CourseUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    start: Optional[datetime] = None
    end: Optional[datetime] = None
    student_id: Optional[int] = None
    price: Optional[float] = Field(None, ge=0)
    color: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = Field(None, max_length=500)
    location: Optional[str] = Field(None, max_length=200)

    @validator("end")
    def end_must_be_after_start(cls, v, values):
        if v and "start" in values and values["start"] and v <= values["start"]:
            raise ValueError("End time must be after start time")
        return v

class Course(CourseBase):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # Computed field - not stored in DB, added during serialization
    student_name: Optional[str] = None
    student_grade: Optional[str] = None

    class Config:
        json_encoders = {}
