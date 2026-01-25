from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from .models import Course, CourseCreate, CourseUpdate, Student, StudentCreate, StudentUpdate
from . import service
from . import ai_service

app = FastAPI(title="Hello Kitty Tutoring Schedule")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== Course Routes ====================

@app.get("/api/courses", response_model=List[Course])
def list_courses():
    return service.get_all_courses()

@app.post("/api/courses", response_model=Course)
def create_course(course: CourseCreate):
    return service.create_course(course)

@app.put("/api/courses/{course_id}", response_model=Course)
def update_course(course_id: str, course: CourseUpdate):
    updated = service.update_course(course_id, course)
    if not updated:
        raise HTTPException(status_code=404, detail="Course not found")
    return updated

@app.delete("/api/courses/{course_id}")
def delete_course(course_id: str):
    success = service.delete_course(course_id)
    if not success:
        raise HTTPException(status_code=404, detail="Course not found")
    return {"status": "success"}

# ==================== Student Routes ====================

@app.get("/api/students", response_model=List[Student])
def list_students():
    return service.get_all_students()

@app.post("/api/students", response_model=Student)
def create_student(student: StudentCreate):
    return service.create_student(student)

@app.get("/api/students/{student_id}", response_model=Student)
def get_student(student_id: int):
    student = service.get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    return student

@app.put("/api/students/{student_id}", response_model=Student)
def update_student(student_id: int, student: StudentUpdate):
    updated = service.update_student(student_id, student)
    if not updated:
        raise HTTPException(status_code=404, detail="Student not found")
    return updated

@app.delete("/api/students/{student_id}")
def delete_student(student_id: int):
    success = service.delete_student(student_id)
    if not success:
        raise HTTPException(status_code=404, detail="Student not found")
    return {"status": "success"}

# ==================== AI Chat Endpoint ====================

@app.post("/api/ai/chat")
async def chat_with_ai(message: str = Body(..., embed=True)):
    return StreamingResponse(
        ai_service.process_chat_stream(message),
        media_type="application/json"
    )


# Mount static files (Frontend)
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=9001, reload=True)
