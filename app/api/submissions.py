from uuid import UUID
from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from bson import ObjectId
import os

from app.schemas.submissions import (
    SubmissionCreate,
    SubmissionUpdate,
    SubmissionOut,
    SubmissionPayload,
)
from app.core.db import get_db, mongo_db
from app.models.postgre import Submission

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


# --------- Helpers ---------
def _coerce_objid(x: Any) -> Any:
    if isinstance(x, ObjectId):
        return str(x)
    if isinstance(x, list):
        return [_coerce_objid(i) for i in x]
    if isinstance(x, dict):
        return {k: _coerce_objid(v) for k, v in x.items()}
    return x

def serialize_mongo(doc: Dict[str, Any] | None) -> Dict[str, Any] | None:
    if not doc:
        return None
    return _coerce_objid(dict(doc))

def get_ai() -> AsyncOpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        # Fail the request cleanly instead of crashing at import time
        raise HTTPException(500, "OPENAI_API_KEY is not set on the server")
    return AsyncOpenAI(api_key=api_key)


# --------- Routes ---------
@router.get("/{uuid}", response_model=SubmissionOut)
async def get_submission(uuid: UUID, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(Submission).where(Submission.uuid == uuid))
    sub = res.scalars().first()
    if not sub:
        raise HTTPException(status_code=404, detail="Submission not found")

    payload_doc: Dict[str, Any] | None = None
    if sub.mongo_id:
        raw = await mongo_db["submissions"].find_one({"_id": ObjectId(sub.mongo_id)})
        payload_doc = serialize_mongo(raw)
        if payload_doc:
            # If your SubmissionPayload doesn't include _id, drop it
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


@router.post("", response_model=SubmissionOut, status_code=status.HTTP_201_CREATED)
async def create_submission(
    data: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
    ai: AsyncOpenAI = Depends(get_ai),
):
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

    chat = await ai.chat.completions.create(
        model=OPENAI_MODEL,
        temperature=0.2,
        messages=[
            {"role": "system", "content": TECHNICAL_PERSONA},
            {"role": "user", "content": prompt_text},
        ],
    )
    ai_text = chat.choices[0].message.content

    payload_for_response: Dict[str, Any] = {**user_input, "ai_response": ai_text}
    to_insert = dict(payload_for_response)
    ins = await mongo_db["submissions"].insert_one(to_insert)
    mongo_id = str(ins.inserted_id)

    sub = Submission(
        title=data.title,
        status=data.status or "pending",
        language=data.language,
        mongo_id=mongo_id,
    )
    db.add(sub)
    await db.commit()
    await db.refresh(sub)

    clean_payload = _coerce_objid(payload_for_response)
    clean_payload.pop("_id", None)  # ensure no _id if your schema doesn't include it

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

# @router.patch("/{uuid}", response_model=SubmissionOut)
# async def update_submission(uuid: UUID, data: SubmissionUpdate, db: AsyncSession = Depends(get_db)):
#
# @router.delete("/{uuid}", status_code=204)
# async def delete_submission(uuid: UUID, db: AsyncSession = Depends(get_db)):
