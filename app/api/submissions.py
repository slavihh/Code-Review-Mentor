from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
import os
from openai import AsyncOpenAI

from app.schemas.submissions import (
    SubmissionCreate,
    SubmissionWithPayloadOut,
    SubmissionOut
)
from app.core.db import get_mongo_db, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.services.submissions import SubmissionsService
from app.repositories.mongo.submissions import SubmissionsMongoRepo
from app.repositories.postgre.submissions import SubmissionsPgRepo
from app.services.ai import get_ai, AI as AIService

router = APIRouter(prefix="/submissions", tags=["submissions"])


def get_pg_repo(session: AsyncSession = Depends(get_db)) -> SubmissionsPgRepo:
    return SubmissionsPgRepo(session)


def get_mg_repo(db=Depends(get_mongo_db)) -> SubmissionsMongoRepo:
    return SubmissionsMongoRepo(db)

def get_submissions_service(
    pg: SubmissionsPgRepo = Depends(get_pg_repo),
    mg: SubmissionsMongoRepo = Depends(get_mg_repo),
    ai: AIService = Depends(get_ai),
) -> SubmissionsService:
    return SubmissionsService(pg=pg, mg=mg, ai=ai)


@router.get("/{uuid}", response_model=SubmissionWithPayloadOut)
async def get_submission(
    uuid: UUID, service: SubmissionsService = Depends(get_submissions_service)
):
    return await service.get(uuid=uuid)


@router.post("", response_model=SubmissionWithPayloadOut, status_code=status.HTTP_201_CREATED)
async def create_submission(
    data: SubmissionCreate,
    service: SubmissionsService = Depends(get_submissions_service),
):
    return await service.create(data)


@router.get("", response_model=List[SubmissionOut])
async def get_submissions(
    service: SubmissionsService = Depends(get_submissions_service)
):
    return await service.getAll()
