
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from app.services.ai import get_ai, AI as AIService
from app.schemas.ai import Review

router = APIRouter()


@router.post("/review")
async def review_code(data: Review, service: AIService = Depends(get_ai)):
    return StreamingResponse(service.stream_feedback(data, data.payload.model_dump()), media_type="text/plain")