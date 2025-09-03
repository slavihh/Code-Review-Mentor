import pytest
from unittest.mock import AsyncMock
from typing import AsyncGenerator
import httpx

from app.services.ai import AI
from app.schemas.ai import ReviewPayload
from app.schemas.submissions import CodePayload
from app.models.postgre import Language
from openai import RateLimitError, APIError


@pytest.fixture
def sample_payload():
    return ReviewPayload(
        language=Language.PYTHON,
        payload=CodePayload(
            content="print('this is a test for my AI service implementation')"
        ),
    )


def make_fake_response(status_code: int = 429) -> httpx.Response:
    return httpx.Response(
        status_code=status_code, request=httpx.Request("GET", "https://test")
    )


@pytest.mark.asyncio
async def test_get_feedback_success(sample_payload):
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = AsyncMock(
        choices=[AsyncMock(message=AsyncMock(content="All good"))]
    )

    ai = AI(ai_client=mock_client)

    result = await ai.get_feedback(sample_payload)
    assert result == "All good"


@pytest.mark.asyncio
async def test_get_feedback_rate_limit_error(sample_payload):
    mock_client = AsyncMock()
    mock_client.chat.completions.create.side_effect = RateLimitError(
        "rate limited", response=make_fake_response(429), body=None
    )

    ai = AI(ai_client=mock_client)

    result = await ai.get_feedback(sample_payload)
    assert "Too many requests" in result


@pytest.mark.asyncio
async def test_stream_feedback_api_error(sample_payload):
    mock_client = AsyncMock()
    mock_client.chat.completions.create.side_effect = APIError(
        message="boom",
        request=httpx.Request("GET", "https://test"),
        body={"error": {"message": "Server error"}},
    )

    ai = AI(ai_client=mock_client)

    chunks = []
    async for chunk in ai.stream_feedback(sample_payload):
        chunks.append(chunk.decode())

    assert "AI service error" in "".join(chunks)


@pytest.mark.asyncio
async def test_stream_feedback_success(sample_payload):
    async def mock_stream() -> AsyncGenerator:
        yield AsyncMock(choices=[AsyncMock(delta=AsyncMock(content="Hello "))])
        yield AsyncMock(choices=[AsyncMock(delta=AsyncMock(content="World"))])

    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = mock_stream()

    ai = AI(ai_client=mock_client)

    chunks = []
    async for chunk in ai.stream_feedback(sample_payload):
        chunks.append(chunk.decode())

    assert "".join(chunks) == "Hello World"


def test_build_messages_success(sample_payload):
    mock_client = AsyncMock()
    mock_client.chat.completions.create.return_value = AsyncMock()
    ai = AI(ai_client=mock_client)
    messages = ai.build_messages(sample_payload)

    assert len(messages) == 2

    assert messages[0]["role"] == "system"
    assert AI.TECHNICAL_PERSONA in messages[0]["content"]
    assert messages[1]["role"] == "user"
    assert "Act as a senior backend engineer." in messages[1]["content"]
    assert (
        "print('this is a test for my AI service implementation')"
        in messages[1]["content"]
    )
