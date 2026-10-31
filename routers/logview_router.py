# routers/logview_router.py
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from utils.sse_log_helper import log_stream_generator

router = APIRouter()


@router.get("/stream")
async def log_stream():
    """SSE实时日志流"""
    return StreamingResponse(log_stream_generator(), media_type="text/event-stream")
