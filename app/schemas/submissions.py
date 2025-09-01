from pydantic import BaseModel, Field
from typing import Any, Optional
from datetime import datetime
from uuid import UUID
from app.models.postgre import Language


class SubmissionPayload(BaseModel):
    content: Any | None = None
    ai_response: Optional[str] = None

    class Config:
        extra = "allow"  # <- let Mongo fields like _id pass through


class SubmissionCreate(BaseModel):
    title: str = Field(..., max_length=255)
    status: Optional[str] = Field(default="pending")
    language: Language
    payload: SubmissionPayload


class SubmissionUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    status: Optional[str] = None
    payload: Optional[SubmissionPayload] = None


class SubmissionOut(BaseModel):
    id: int
    uuid: UUID
    title: str
    status: str
    language: Language
    mongo_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    payload: Optional[SubmissionPayload] = None

    class Config:
        from_attributes = True
