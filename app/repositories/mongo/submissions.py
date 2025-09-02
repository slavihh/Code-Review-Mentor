from typing import Any, Dict, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson import ObjectId


class SubmissionsMongoRepo:
    def __init__(self, db: AsyncIOMotorDatabase):
        self.db = db

    async def find(self, mongo_id: str) -> Optional[Dict[str, Any]]:
        raw = await self.db["submissions"].find_one({"_id": ObjectId(mongo_id)})

        return self.serialize_mongo(raw)

    async def find_all(self) -> Optional[Dict[str, Any]]:
        submissions_dict = {}
        async for doc in self.db["submissions"].find({}):
            submissions_dict[str(doc["_id"])] = doc
        return submissions_dict

    async def insert(self, user_input: dict[str, Any], ai_text: str | None) -> str:
        payload_for_response: Dict[str, Any] = {**user_input, "ai_response": ai_text}
        to_insert = dict(payload_for_response)
        ins = await self.db["submissions"].insert_one(to_insert)

        return str(ins.inserted_id)

    def serialize_mongo(self, doc: Dict[str, Any] | None) -> Dict[str, Any] | None:
        if not doc:
            return None
        return self._coerce_objid(dict(doc))

    def _coerce_objid(self, x: Any) -> Any:
        if isinstance(x, ObjectId):
            return str(x)
        if isinstance(x, list):
            return [self._coerce_objid(i) for i in x]
        if isinstance(x, dict):
            return {k: self._coerce_objid(v) for k, v in x.items()}
        return x
