from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from app.core.di import GetAIService
from app.schemas.ai import ReviewPayload

router = APIRouter()


@router.post("/review")
async def review_code(data: ReviewPayload, service: GetAIService):
    return StreamingResponse(service.stream_feedback(data), media_type="text/plain")
