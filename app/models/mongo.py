from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from bson import ObjectId
from pydantic import GetCoreSchemaHandler
from pydantic_core import core_schema


class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler: GetCoreSchemaHandler):
        return core_schema.no_info_after_validator_function(
            cls.validate,
            core_schema.str_schema(),
            serialization=core_schema.plain_serializer_function_ser_schema(str),
        )

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)


class SubmissionDocument(BaseModel):
    id: Optional[str] = Field(alias="_id")
    content: str
    ai_response: Optional[str] = None

    model_config = ConfigDict(populate_by_name=True)
