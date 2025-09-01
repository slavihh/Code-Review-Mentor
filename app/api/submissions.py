from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
import os

from app.schemas.submissions import (
    SubmissionCreate,
    SubmissionOut,
)
from app.core.db import get_db, get_mongo_db
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.submissions import SubmissionsService
from app.repositories.mongo.submissions import SubmissionsMongoRepo
from app.repositories.postgre.submissions import SubmissionsPgRepo

# OpenAI (async client)
from openai import AsyncOpenAI

TECHNICAL_PERSONA = (
    "You are a senior backend engineer and code reviewer. "
    "Be concise, specific, and pragmatic. "
    "Return actionable bullet points. "
    "When suggesting fixes, include minimal, correct code snippets."
)
OPENAI_MODEL = "gpt-4o-mini"

router = APIRouter(prefix="/submissions", tags=["submissions"])


def get_pg_repo(session: AsyncSession = Depends(get_db)) -> SubmissionsPgRepo:
    return SubmissionsPgRepo(session)


def get_mg_repo(db=Depends(get_mongo_db)) -> SubmissionsMongoRepo:
    return SubmissionsMongoRepo(db)


def get_ai() -> AsyncOpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(500, "OPENAI_API_KEY is not set on the server")
    return AsyncOpenAI(api_key=api_key)


def get_submissions_service(
    pg: SubmissionsPgRepo = Depends(get_pg_repo),
    mg: SubmissionsMongoRepo = Depends(get_mg_repo),
    ai: AsyncOpenAI = Depends(get_ai),
) -> SubmissionsService:
    return SubmissionsService(pg=pg, mg=mg, ai=ai)


@router.get("/{uuid}", response_model=SubmissionOut)
async def get_submission(
    uuid: UUID, service: SubmissionsService = Depends(get_submissions_service)
):
    return await service.get(uuid=uuid)


@router.post("", response_model=SubmissionOut, status_code=status.HTTP_201_CREATED)
async def create_submission(
    data: SubmissionCreate,
    service: SubmissionsService = Depends(get_submissions_service),
):
    return await service.create(data)


# @router.patch("/{uuid}", response_model=SubmissionOut)
# async def update_submission(uuid: UUID, data: SubmissionUpdate, db: AsyncSession = Depends(get_db)):
#
# @router.delete("/{uuid}", status_code=204)
# async def delete_submission(uuid: UUID, db: AsyncSession = Depends(get_db)):
