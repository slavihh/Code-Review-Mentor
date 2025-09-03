import pytest
from uuid import uuid4
from datetime import datetime, UTC
from fastapi import HTTPException
from unittest.mock import AsyncMock
from typing import cast

from app.models.postgre import Language
from app.services.submissions import SubmissionsService, _coerce_objid
from app.schemas.submissions import SubmissionCreate, CodePayload
from app.repositories.protocols import SubmissionsPGRepo, SubmissionsMongoRepo
from app.services.ai import AI as AIService
import hashlib


@pytest.mark.asyncio
async def test_coerce_objid():
    from bson import ObjectId

    objid = ObjectId()
    data = {"id": objid, "list": [objid, {"nested": objid}]}
    result = _coerce_objid(data)
    assert isinstance(result["id"], str)
    assert isinstance(result["list"][0], str)
    assert isinstance(result["list"][1]["nested"], str)


class FakePgSubmission:
    def __init__(self, mongo_id=None):
        self.id = 1
        self.uuid = uuid4()
        self.title = "test"
        self.language = Language.PYTHON
        self.mongo_id = mongo_id
        self.created_at = datetime.now(UTC)
        self.updated_at = datetime.now(UTC)


@pytest.mark.asyncio
async def test_get_submission_with_payload():
    fake_pg = cast(SubmissionsPGRepo, AsyncMock(spec=SubmissionsPGRepo))
    fake_mg = cast(SubmissionsMongoRepo, AsyncMock(spec=SubmissionsMongoRepo))
    fake_ai = cast(AIService, AsyncMock(spec=AIService))

    fake_submission = FakePgSubmission(mongo_id="abc123")
    fake_pg.find_by_uuid.return_value = fake_submission
    fake_mg.find.return_value = {
        "_id": "abc123",
        "content": "print('Testing submissions service implementation to prevent errors')",
        "ai_response": "Looks good",
    }

    service = SubmissionsService(pg=fake_pg, mg=fake_mg, ai=fake_ai)

    result = await service.get(fake_submission.uuid)

    assert result.title == "test"
    assert (
        result.payload.content
        == "print('Testing submissions service implementation to prevent errors')"
    )
    assert result.payload.ai_response == "Looks good"


@pytest.mark.asyncio
async def test_get_submission_not_found():
    fake_pg = cast(SubmissionsPGRepo, AsyncMock(spec=SubmissionsPGRepo))
    fake_pg.find_by_uuid.return_value = None

    service = SubmissionsService(
        pg=fake_pg,
        mg=cast(SubmissionsMongoRepo, AsyncMock(spec=SubmissionsMongoRepo)),
        ai=cast(AIService, AsyncMock(spec=AIService)),
    )

    with pytest.raises(HTTPException) as excinfo:
        await service.get(uuid4())

    assert excinfo.value.status_code == 404


@pytest.mark.asyncio
async def test_get_all_submissions():
    fake_pg = cast(SubmissionsPGRepo, AsyncMock(spec=SubmissionsPGRepo))
    fake_pg.find_all.return_value = [FakePgSubmission(), FakePgSubmission()]

    service = SubmissionsService(
        pg=fake_pg,
        mg=cast(SubmissionsMongoRepo, AsyncMock(spec=SubmissionsMongoRepo)),
        ai=cast(AIService, AsyncMock(spec=AIService)),
    )

    result = await service.get_all()
    assert len(result) == 2
    assert all(r.title == "test" for r in result)


@pytest.mark.asyncio
async def test_create_submission():
    fake_pg = cast(SubmissionsPGRepo, AsyncMock(spec=SubmissionsPGRepo))
    fake_mg = cast(SubmissionsMongoRepo, AsyncMock(spec=SubmissionsMongoRepo))
    fake_ai = cast(AIService, AsyncMock(spec=AIService))

    fake_ai.get_feedback.return_value = "AI says OK"
    fake_pg.find_by_hash.return_value = None
    fake_mg.insert.return_value = {
        "_id": "mongo123",
        "content": "print('Testing submissions service implementation to prevent errors')",
        "ai_response": "AI says OK",
    }
    fake_pg.create.return_value = FakePgSubmission(mongo_id="mongo123")

    service = SubmissionsService(pg=fake_pg, mg=fake_mg, ai=fake_ai)

    data = SubmissionCreate(
        title="test",
        language=Language.PYTHON,
        payload=CodePayload(
            content="print('Testing submissions service implementation to prevent errors')"
        ),
    )

    result = await service.create(data)

    assert result.title == "test"
    assert (
        result.payload.content
        == "print('Testing submissions service implementation to prevent errors')"
    )
    assert result.payload.ai_response == "AI says OK"


@pytest.mark.asyncio
async def test_create_submission_existing_in_db():
    fake_pg = cast(SubmissionsPGRepo, AsyncMock(spec=SubmissionsPGRepo))
    fake_mg = cast(SubmissionsMongoRepo, AsyncMock(spec=SubmissionsMongoRepo))
    fake_ai = cast(AIService, AsyncMock(spec=AIService))

    service = SubmissionsService(pg=fake_pg, mg=fake_mg, ai=fake_ai)

    content = "print('Testing submissions service implementation to prevent errors')"
    data = SubmissionCreate(
        title="test",
        language=Language.PYTHON,
        payload=CodePayload(content=content),
    )

    expected_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()

    existing_sub = FakePgSubmission(mongo_id="mongo123")
    fake_pg.find_by_hash.return_value = existing_sub
    fake_mg.find = AsyncMock(
        return_value={
            "_id": "mongo123",
            "content": content,
            "ai_response": "Already exists!",
        }
    )

    result = await service.create(data)

    fake_pg.find_by_hash.assert_awaited_once_with(expected_hash)
    fake_pg.create.assert_not_called()
    fake_ai.get_feedback.assert_not_called()
    fake_mg.insert.assert_not_called()

    assert result.payload.content == content
    assert result.payload.ai_response == "Already exists!"
