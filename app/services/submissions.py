from typing import Any, Dict, List
from uuid import UUID
from bson import ObjectId
from fastapi import HTTPException

from app.models.postgre import Submission
from app.schemas.submissions import (
    SubmissionWithPayloadOut,
    CodePayload,
    SubmissionCreate,
)
from app.repositories.protocols import SubmissionsPGRepo, SubmissionsMongoRepo
from app.services.ai import AI as AIService
import hashlib


def _coerce_objid(x):
    if isinstance(x, ObjectId):
        return str(x)
    if isinstance(x, list):
        return [_coerce_objid(i) for i in x]
    if isinstance(x, dict):
        return {k: _coerce_objid(v) for k, v in x.items()}
    return x


def build_submission_with_payload(
    sub: Submission, user_input: dict[str, Any], ai_text: str
) -> SubmissionWithPayloadOut:
    payload_for_response: Dict[str, Any] = {**user_input, "ai_response": ai_text}
    clean_payload = _coerce_objid(payload_for_response)
    clean_payload.pop("_id", None)
    return SubmissionWithPayloadOut(
        id=sub.id,
        uuid=sub.uuid,
        title=sub.title,
        language=sub.language,
        mongo_id=sub.mongo_id,
        created_at=sub.created_at,
        updated_at=sub.updated_at,
        payload=CodePayload(**clean_payload),
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

        payload_doc = None
        if sub.mongo_id:
            raw = await self.mg.find(sub.mongo_id)
            payload_doc = _coerce_objid(raw) if raw else None
            if payload_doc:
                payload_doc.pop("_id", None)

        return SubmissionWithPayloadOut(
            id=sub.id,
            uuid=sub.uuid,
            title=sub.title,
            language=sub.language,
            mongo_id=sub.mongo_id,
            created_at=sub.created_at,
            updated_at=sub.updated_at,
            payload=CodePayload(**payload_doc) if payload_doc else None,
        )

    async def getAll(self) -> List[SubmissionWithPayloadOut]:
        pg_submissions = await self.pg.find_all()
        result = []
        for sub in pg_submissions:
            submission = SubmissionWithPayloadOut(
                id=sub.id,
                uuid=sub.uuid,
                title=sub.title,
                language=sub.language,
                mongo_id=sub.mongo_id,
                created_at=sub.created_at,
                updated_at=sub.updated_at,
            )
            result.append(submission)
        return result

    async def create(self, data: SubmissionCreate) -> SubmissionWithPayloadOut:
        user_input = data.payload.model_dump()
        content = user_input.get("content")
        if not content:
            raise HTTPException(400, "Content field is required")
        code_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        check_submission = await self.pg.find_by_hash(code_hash)
        # return already submitted AI response based on hash
        if check_submission and check_submission.mongo_id is not None:
            raw = await self.mg.find(str(check_submission.mongo_id))
            payload_doc = _coerce_objid(raw) if raw else None
            if payload_doc:
                payload_doc.pop("_id", None)
                print(payload_doc.keys())
                return build_submission_with_payload(
                    check_submission, user_input, payload_doc["ai_response"]
                )
        ai_text = await self.ai.get_feedback(data=data)
        if not ai_text:
            ai_text = ""
        mongo_id = await self.mg.insert(user_input, ai_text)

        sub = await self.pg.create(
            title=data.title,
            language=data.language,
            mongo_id=mongo_id,
            code_hash=code_hash,
        )

        return build_submission_with_payload(sub, user_input, ai_text)
