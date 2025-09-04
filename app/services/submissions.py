import hashlib
import logging
from typing import Any, Dict, List, Optional
from uuid import UUID
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError
from pymongo.errors import PyMongoError

from app.models.postgre import Submission
from app.schemas.submissions import (
    SubmissionWithPayloadOut,
    CodePayload,
    SubmissionCreate,
    SubmissionOut,
)
from app.repositories.protocols import SubmissionsPgRepo, SubmissionsMongoRepo
from app.models.mongo import SubmissionDocument
from app.services.ai import AI as AIService

logger = logging.getLogger("app.services.submissions")


def build_submission_with_payload(
    sub: Submission, user_input: dict[str, Any], ai_text: str
) -> SubmissionWithPayloadOut:
    payload_for_response: Dict[str, Any] = {**user_input, "ai_response": ai_text}
    return SubmissionWithPayloadOut(
        uuid=sub.uuid,
        title=sub.title,
        language=sub.language,
        created_at=sub.created_at,
        updated_at=sub.updated_at,
        payload=CodePayload(**payload_for_response),
    )


class SubmissionsService:
    def __init__(self, pg: SubmissionsPgRepo, mg: SubmissionsMongoRepo, ai: AIService):
        self.pg = pg
        self.mg = mg
        self.ai = ai

    async def get(self, uuid: UUID) -> SubmissionWithPayloadOut:
        logger.info(f"Fetching submission by UUID: {uuid}")
        try:
            sub = await self.pg.find_by_uuid(uuid)
        except Exception:
            logger.exception(f"Error occurred while fetching submission {uuid}")
            raise HTTPException(500, "Error occurred")

        if not sub:
            logger.warning(f"Submission not found: {uuid}")
            raise HTTPException(404, "Submission not found")

        payload_doc: Optional[SubmissionDocument] = None
        if sub.mongo_id:
            try:
                logger.debug(f"Fetching Mongo payload for submission {sub.id}")
                payload_doc = await self.mg.find(sub.mongo_id)
            except Exception:
                logger.exception(
                    f"Error fetching Mongo payload for submission {sub.id}"
                )

        return SubmissionWithPayloadOut(
            uuid=sub.uuid,
            title=sub.title,
            language=sub.language,
            created_at=sub.created_at,
            updated_at=sub.updated_at,
            payload=(
                CodePayload(**payload_doc.model_dump(by_alias=True, exclude_none=True))
                if payload_doc
                else None
            ),
        )

    async def get_all(self) -> List[SubmissionOut]:
        logger.info("Fetching all submissions from Postgres")
        try:
            pg_submissions = await self.pg.find_all()
        except Exception:
            logger.exception("Error occurred while fetching all submissions")
            raise HTTPException(500, "Error occurred")

        result = [
            SubmissionOut(
                uuid=sub.uuid,
                title=sub.title,
                language=sub.language,
                created_at=sub.created_at,
                updated_at=sub.updated_at,
                short_feedback=sub.short_feedback,
            )
            for sub in pg_submissions
        ]
        logger.info(f"Retrieved {len(result)} submissions")
        return result

    async def create(self, data: SubmissionCreate) -> SubmissionWithPayloadOut:
        logger.info(
            f"Creating new submission with title={data.title}, language={data.language}"
        )
        user_input = data.payload.model_dump()
        content = user_input.get("content")
        if not content:
            logger.warning("Submission create failed: missing content field")
            raise HTTPException(400, "Content field is required")

        code_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
        logger.debug(f"Generated hash {code_hash} for submission content")

        try:
            check_submission = await self.pg.find_by_hash(code_hash)
        except Exception:
            logger.exception("Error occurred while checking submission hash")
            raise HTTPException(500, "Error occurred")

        if check_submission and check_submission.mongo_id is not None:
            try:
                logger.info(
                    f"Duplicate submission detected (hash={code_hash}), returning cached result"
                )
                payload_doc = await self.mg.find(str(check_submission.mongo_id))
                if payload_doc:
                    return build_submission_with_payload(
                        check_submission,
                        user_input,
                        payload_doc.ai_response or "",
                    )
            except PyMongoError:
                logger.exception("Error fetching cached Mongo payload")
        short_feedback = ""
        try:
            ai_text = await self.ai.get_feedback(data=data) or ""
            short_feedback = (ai_text[:62] + "..") if len(ai_text) > 62 else ai_text
            logger.info("AI feedback generated successfully")
        except Exception:
            logger.exception("AI feedback generation failed")
            ai_text = ""

        mongo_id: Optional[str] = None
        try:
            mongo_id = await self.mg.insert(user_input, ai_text)
            logger.info(f"Inserted payload into MongoDB with id={mongo_id}")
        except PyMongoError:
            logger.exception("Mongo insert failed — aborting request")

        if mongo_id:
            try:
                sub = await self.pg.create(
                    title=data.title,
                    language=data.language,
                    mongo_id=mongo_id,
                    code_hash=code_hash,
                    short_feedback=short_feedback,
                )
                logger.info(f"Submission stored in Postgres with id={sub.id}")
            except SQLAlchemyError:
                logger.exception("Error occurred while creating submission")
                raise HTTPException(500, "Error occurred")
        else:
            raise HTTPException(500, "Error occurred while inserting in database")

        return build_submission_with_payload(sub, user_input, ai_text)
