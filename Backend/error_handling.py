from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger(__name__)

async def validation_exception_handler(request: Request, exc: Exception):
    logger.error(f"Validation error: {str(exc)}")
    return JSONResponse(
        status_code=400,
        content={"status": "fail", "message": "Invalid request format"},
    )

async def ai_response_handler(request: Request, exc: Exception):
    logger.error(f"AI processing failed: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "AI service unavailable"},
    )

def handle_database_error(exc: Exception):
    logger.error(f"Database error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "Database operation failed"}
    )

def handle_index_error(exc: IndexError):
    logger.error(f"Index error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "Data format mismatch"}
    )