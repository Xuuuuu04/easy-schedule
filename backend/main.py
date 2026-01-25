from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
from .models import Course, CourseCreate, CourseUpdate, Student, StudentCreate, StudentUpdate
from . import service
from . import ai_service
from .config import settings
import logging

app = FastAPI(title="Hello Kitty Tutoring Schedule")

# Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
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
def list_students(
    limit: int = 100,
    offset: int = 0,
    name: Optional[str] = None
):
    return service.get_all_students(limit=limit, offset=offset, name_filter=name)

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
async def chat_with_ai(request: Request, message: str = Body(..., embed=True)):
    session_id = request.headers.get("X-Session-ID") or "user-session-1"
    return StreamingResponse(
        ai_service.process_chat_stream(message, session_id),
        media_type="application/x-ndjson"
    )


@app.get("/healthz")
def healthz():
    return {"status": "ok"}

@app.get("/readyz")
def readyz():
    # 简化：如果可读取学生列表则认为就绪
    try:
        _ = service.get_all_students()
        return {"status": "ready"}
    except Exception:
        return {"status": "degraded"}

# Mount static files (Frontend) - MUST be last
app.mount("/", StaticFiles(directory="frontend", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=9001, reload=True)
