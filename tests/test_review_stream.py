import pytest
import httpx
from app.main import app

from httpx import ASGITransport


@pytest.mark.asyncio
async def test_streaming_review():
    transport = ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        async with client.stream(
            "POST",
            "/review",
            json={"language": "Python", "payload": {"content": "print(123)"}},
        ) as response:
            assert response.status_code == 200

            chunks = []
            async for chunk in response.aiter_text():
                chunks.append(chunk)

            full_output = "".join(chunks)
            assert "print(123)" in full_output or "Python" in full_output
