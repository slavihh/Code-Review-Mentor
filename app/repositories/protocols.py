from typing import Protocol, Any, Optional, Dict
from uuid import UUID
from app.models.postgre import Submission


class SubmissionsPGRepo(Protocol):
    async def get_by_uuid(self, uuid: UUID) -> Optional["Submission"]: ...
    async def create(
        self, *, title: str, status: str, language: str, mongo_id: str
    ) -> "Submission": ...


class SubmissionsMongoRepo(Protocol):
    async def get(self, mongo_id: str) -> Optional[Dict[str, Any]]: ...
    async def insert(self, user_input: Dict[str, Any], ai_text: str | None) -> str: ...
