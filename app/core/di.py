from app.core.db import get_mongo_db, get_db
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from typing import Annotated, TypeAlias
from app.services.submissions import SubmissionsService
from app.repositories.mongo.submissions import SubmissionsMongoRepo
from app.repositories.postgre.submissions import SubmissionsPgRepo
import os
from app.services.ai import AI as AIService
from openai import AsyncOpenAI


def get_pg_repo(session: AsyncSession = Depends(get_db)) -> SubmissionsPgRepo:
    return SubmissionsPgRepo(session)


def get_mg_repo(db=Depends(get_mongo_db)) -> SubmissionsMongoRepo:
    return SubmissionsMongoRepo(db)


def get_ai() -> AIService:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise Exception(500, "OPENAI_API_KEY is not set on the server")
    return AIService(AsyncOpenAI(api_key=api_key))


def get_submissions_service(
    pg: SubmissionsPgRepo = Depends(get_pg_repo),
    mg: SubmissionsMongoRepo = Depends(get_mg_repo),
    ai: AIService = Depends(get_ai),
) -> SubmissionsService:
    return SubmissionsService(pg=pg, mg=mg, ai=ai)


GetSubmissionsService: TypeAlias = Annotated[
    SubmissionsService, Depends(get_submissions_service)
]
GetAIService: TypeAlias = Annotated[AIService, Depends(get_ai)]
