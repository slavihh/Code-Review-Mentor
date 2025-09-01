from typing import Any, Dict
from uuid import UUID
from bson import ObjectId
from fastapi import HTTPException
from openai import AsyncOpenAI

from app.schemas.submissions import SubmissionOut, SubmissionPayload
from app.repositories.protocols import SubmissionsPGRepo, SubmissionsMongoRepo


def _coerce_objid(x):
    if isinstance(x, ObjectId):
        return str(x)
    if isinstance(x, list):
        return [_coerce_objid(i) for i in x]
    if isinstance(x, dict):
        return {k: _coerce_objid(v) for k, v in x.items()}
    return x


TECHNICAL_PERSONA = (
    "You are a senior backend engineer and code reviewer. "
    "Be concise, specific, and pragmatic. "
    "Return actionable bullet points. "
    "When suggesting fixes, include minimal, correct code snippets."
)
OPENAI_MODEL = "gpt-4o-mini"


class SubmissionsService:
    def __init__(
        self, pg: SubmissionsPGRepo, mg: SubmissionsMongoRepo, ai: AsyncOpenAI
    ):
        self.pg = pg
        self.mg = mg
        self.ai = ai

    async def get(self, uuid: UUID) -> SubmissionOut:
        sub = await self.pg.get_by_uuid(uuid)
        if not sub:
            raise HTTPException(404, "Submission not found")

        payload_doc = None
        if sub.mongo_id:
            raw = await self.mg.get(sub.mongo_id)
            payload_doc = _coerce_objid(raw) if raw else None
            if payload_doc:
                payload_doc.pop("_id", None)

        return SubmissionOut(
            id=sub.id,
            uuid=sub.uuid,
            title=sub.title,
            status=sub.status,
            language=sub.language,
            mongo_id=sub.mongo_id,
            created_at=sub.created_at,
            updated_at=sub.updated_at,
            payload=SubmissionPayload(**payload_doc) if payload_doc else None,
        )

    async def create(self, data) -> SubmissionOut:
        user_input = data.payload.model_dump()
        prompt_text = (
            f"Act as a senior backend engineer. "
            f"Analyze this {data.language} code for backend issues. "
            "Format response as:\n\n"
            "1. Brief summary (1 sentence)\n"
            "2. Key findings (bulleted list)\n"
            "3. Most critical recommendation\n"
            "Avoid markdown. Be technical but concise."
        )
        chat = await self.ai.chat.completions.create(
            model=OPENAI_MODEL,
            temperature=0.2,
            messages=[
                {"role": "system", "content": TECHNICAL_PERSONA},
                {
                    "role": "user",
                    "content": f"{prompt_text}\n\n{user_input.get('content')}",
                },
            ],
        )
        ai_text = chat.choices[0].message.content
        payload_for_response: Dict[str, Any] = {**user_input, "ai_response": ai_text}
        mongo_id = await self.mg.insert(user_input, ai_text)

        sub = await self.pg.create(
            title=data.title,
            status=data.status or "pending",
            language=data.language,
            mongo_id=mongo_id,
        )

        clean_payload = _coerce_objid(payload_for_response)
        clean_payload.pop("_id", None)

        return SubmissionOut(
            id=sub.id,
            uuid=sub.uuid,
            title=sub.title,
            status=sub.status,
            language=sub.language,
            mongo_id=sub.mongo_id,
            created_at=sub.created_at,
            updated_at=sub.updated_at,
            payload=SubmissionPayload(**clean_payload),
        )
