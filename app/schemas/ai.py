from app.schemas.submissions import CodePayload
from pydantic import BaseModel
from app.models.postgre import Language


class ReviewPayload(BaseModel):
    language: Language
    payload: CodePayload