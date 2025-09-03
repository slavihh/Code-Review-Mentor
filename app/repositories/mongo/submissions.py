from typing import Any, Dict, Optional, List
from bson import ObjectId
from app.models.mongo import SubmissionDocument
from motor.motor_asyncio import AsyncIOMotorDatabase


class SubmissionsMongoRepo:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def find(self, mongo_id: str) -> Optional[SubmissionDocument]:
        raw = await self.db["submissions"].find_one({"_id": ObjectId(mongo_id)})
        if raw:
            raw["_id"] = str(raw["_id"])
            return SubmissionDocument(**raw)
        return None

    async def find_all(self) -> List[SubmissionDocument]:
        results = []
        async for doc in self.db["submissions"].find({}):
            results.append(SubmissionDocument(**doc))
        return results

    async def insert(self, user_input: dict[str, Any], ai_text: str | None) -> str:
        payload_for_response: Dict[str, Any] = {**user_input, "ai_response": ai_text}
        ins = await self.db["submissions"].insert_one(payload_for_response)
        return str(ins.inserted_id)
