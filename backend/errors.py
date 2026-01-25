from fastapi import Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Any

# ==================== Error Models ====================

class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None

# ==================== Exception Handlers ====================

async def validation_exception_handler(request: Request, exc):
    """Handle Pydantic validation errors"""
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error="Validation Error",
            detail=str(exc),
            code="VALIDATION_ERROR"
        ).dict()
    )

async def http_exception_handler(request: Request, exc):
    """Handle FastAPI HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail if isinstance(exc.detail, str) else "HTTP Error",
            detail=str(exc.detail) if not isinstance(exc.detail, str) else None,
            code=f"HTTP_{exc.status_code}"
        ).dict()
    )

async def generic_exception_handler(request: Request, exc):
    """Handle unexpected server errors"""
    import traceback
    print(traceback.format_exc())  # Log the full stack trace
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail="An unexpected error occurred. Please try again later.",
            code="INTERNAL_SERVER_ERROR"
        ).dict()
    )
