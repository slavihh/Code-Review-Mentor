from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.models.postgre import Submission


class SubmissionsPgRepo:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_uuid(self, uuid: UUID) -> Optional["Submission"]:
        res = await self.db.execute(select(Submission).where(Submission.uuid == uuid))
        return res.scalars().first()

    async def create(
        self, *, title: str, status: str, language: str, mongo_id: str
    ) -> "Submission":
        sub = Submission(
            title=title,
            status=status or "pending",
            language=language,
            mongo_id=mongo_id,
        )
        self.db.add(sub)
        await self.db.commit()
        await self.db.refresh(sub)

        return sub
