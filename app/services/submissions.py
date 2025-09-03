from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import HTTPException
import hashlib

from app.models.postgre import Submission
from app.schemas.submissions import (
    SubmissionWithPayloadOut,
    CodePayload,
    SubmissionCreate,
)
from app.repositories.protocols import SubmissionsPGRepo, SubmissionsMongoRepo
from app.services.ai import AI as AIService
from app.models.mongo import SubmissionDocument


def build_submission_with_payload(
    sub: Submission, user_input: dict[str, Any], ai_text: str
) -> SubmissionWithPayloadOut:
    payload_for_response: Dict[str, Any] = {**user_input, "ai_response": ai_text}
    return SubmissionWithPayloadOut(
        id=sub.id,
        uuid=sub.uuid,
        title=sub.title,
        language=sub.language,
        mongo_id=sub.mongo_id,
        created_at=sub.created_at,
        updated_at=sub.updated_at,
        payload=CodePayload(**payload_for_response),
    )


class SubmissionsService:
    def __init__(self, pg: SubmissionsPGRepo, mg: SubmissionsMongoRepo, ai: AIService):
        self.pg = pg
        self.mg = mg
        self.ai = ai

    async def get(self, uuid: UUID) -> SubmissionWithPayloadOut:
        sub = await self.pg.find_by_uuid(uuid)
        if not sub:
            raise HTTPException(404, "Submission not found")

        payload_doc: Optional[SubmissionDocument] = None
        if sub.mongo_id:
            payload_doc = await self.mg.find(sub.mongo_id)

        return SubmissionWithPayloadOut(
            id=sub.id,
            uuid=sub.uuid,
            title=sub.title,
            language=sub.language,
            mongo_id=sub.mongo_id,
            created_at=sub.created_at,
            updated_at=sub.updated_at,
            payload=CodePayload(**payload_doc.dict(by_alias=True, exclude_none=True))
            if payload_doc
            else None,
        )

    async def getAll(self) -> List[SubmissionWithPayloadOut]:
        pg_submissions = await self.pg.find_all()
        return [
            SubmissionWithPayloadOut(
                id=sub.id,
                uuid=sub.uuid,
                title=sub.title,
                language=sub.language,
                mongo_id=sub.mongo_id,
                created_at=sub.created_at,
                updated_at=sub.updated_at,
            )
            for sub in pg_submissions
        ]

    async def create(self, data: SubmissionCreate) -> SubmissionWithPayloadOut:
        user_input = data.payload.model_dump()
        content = user_input.get("content")
        if not content:
            raise HTTPException(400, "Content field is required")

        code_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        check_submission = await self.pg.find_by_hash(code_hash)

        # if same code already exists in Postgres and Mongo
        if check_submission and check_submission.mongo_id:
            payload_doc = await self.mg.find(check_submission.mongo_id)
            if payload_doc:
                return build_submission_with_payload(
                    check_submission,
                    user_input,
                    payload_doc.ai_response or "",
                )

        ai_text = await self.ai.get_feedback(data=data) or ""
        mongo_id = await self.mg.insert(user_input, ai_text)

        sub = await self.pg.create(
            title=data.title,
            language=data.language,
            mongo_id=mongo_id,
            code_hash=code_hash,
        )

        return build_submission_with_payload(sub, user_input, ai_text)
