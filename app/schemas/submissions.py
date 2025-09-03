from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID
from app.models.postgre import Language


class CodePayload(BaseModel):
    content: str = Field(min_length=30, max_length=500)
    ai_response: Optional[str] = None

    model_config = ConfigDict(extra="allow")


class SubmissionCreate(BaseModel):
    title: str = Field(..., max_length=255)
    language: Language
    payload: CodePayload


class SubmissionUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    payload: Optional[CodePayload] = None


class SubmissionWithPayloadOut(BaseModel):
    uuid: UUID
    title: str
    language: Language
    mongo_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    payload: Optional[CodePayload] = None

    model_config = ConfigDict(from_attributes=True)


class SubmissionOut(BaseModel):
    uuid: UUID
    title: str
    short_feedback: str
    language: Language
    mongo_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime
