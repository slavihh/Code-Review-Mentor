from uuid import UUID
from fastapi import APIRouter, status

from app.schemas.submissions import (
    SubmissionCreate,
    SubmissionWithPayloadOut,
    SubmissionOut,
)
from typing import List
from app.core.di import GetSubmissionsService

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.get("/{uuid}", response_model=SubmissionWithPayloadOut)
async def get_submission(uuid: UUID, service: GetSubmissionsService):
    return await service.get(uuid=uuid)


@router.post(
    "", response_model=SubmissionWithPayloadOut, status_code=status.HTTP_201_CREATED
)
async def create_submission(
    data: SubmissionCreate,
    service: GetSubmissionsService,
):
    return await service.create(data)


@router.get("", response_model=List[SubmissionOut])
async def get_submissions(
    service: GetSubmissionsService,
):
    return await service.get_all()
