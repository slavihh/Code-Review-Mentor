from typing import Optional, Sequence
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.models.postgre import Submission, Language


class SubmissionsPgRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def find_by_uuid(self, uuid: UUID) -> Optional["Submission"]:
        res = await self.db.execute(select(Submission).where(Submission.uuid == uuid))
        return res.scalars().first()

    async def find_by_hash(self, code_hash: str) -> Optional["Submission"]:
        res = await self.db.execute(
            select(Submission).where(Submission.hash == code_hash)
        )
        return res.scalars().first()

    async def find_all(self) -> Sequence["Submission"]:
        res = await self.db.execute(select(Submission))
        return res.scalars().all()

    async def create(
        self, *, title: str, language: Language, mongo_id: str, code_hash: str
    ) -> "Submission":
        sub = Submission(
            title=title,
            language=language,
            mongo_id=mongo_id,
            hash=code_hash,
        )
        self.db.add(sub)
        await self.db.commit()
        await self.db.refresh(sub)

        return sub
