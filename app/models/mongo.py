from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from bson import ObjectId

class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

class FeedbackChunk(BaseModel):
    text: str
    timestamp: Optional[float] = None

class SubmissionDocument(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id")
    submission_id: str
    full_code: str
    full_feedback: Optional[str] = None
    streaming_chunks: Optional[List[FeedbackChunk]] = []
    persona: Optional[str] = None
    token_usage: Optional[Dict[str, int]] = None

    class Config:
        allow_population_by_field_name = True
        json_encoders = {ObjectId: str}
