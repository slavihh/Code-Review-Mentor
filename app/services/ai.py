from typing import Dict, AsyncGenerator
from openai import AsyncOpenAI
import os

def get_ai() -> AsyncOpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise Exception(500, "OPENAI_API_KEY is not set on the server")
    return AI(AsyncOpenAI(api_key=api_key))


class AI:
    TECHNICAL_PERSONA = (
    "You are a senior backend engineer and code reviewer. "
    "Be concise, specific, and pragmatic. "
    "Return actionable bullet points. "
    "When suggesting fixes, include minimal, correct code snippets."
    )
    OPENAI_MODEL = "gpt-4o-mini"

    def __init__(self, ai_client: AsyncOpenAI):
        self.ai_client = ai_client

    async def get_feedback(self, data: Dict[str, any], code_input: Dict[str, any]) -> str:
        prompt_text = (
            f"Act as a senior backend engineer. "
            f"Analyze this {data.language} code for backend issues. "
            "Format response as:\n\n"
            "1. Brief summary (1 sentence)\n"
            "2. Key findings (bulleted list)\n"
            "3. Most critical recommendation\n"
            "Avoid markdown. Be technical but concise."
        )
        chat = await self.ai_client.chat.completions.create(
            model=self.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": self.TECHNICAL_PERSONA},
                {
                    "role": "user",
                    "content": f"{prompt_text}\n\n{code_input.get('content')}",
                },
            ],
        )
        return chat.choices[0].message.content
    

    async def stream_feedback(self, data: Dict[str, any], code_input: Dict[str, any]) -> AsyncGenerator[bytes, None]:
        prompt_text = (
            f"Act as a senior backend engineer. "
            f"Analyze this {data.language} code for backend issues. "
            "Format response as:\n\n"
            "1. Brief summary (1 sentence)\n"
            "2. Key findings (bulleted list)\n"
            "3. Most critical recommendation\n"
            "Avoid markdown. Be technical but concise."
        )

        stream = await self.ai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": self.TECHNICAL_PERSONA},
                {"role": "user", "content": prompt_text},
            ],
            stream=True,
        )

        async for chunk in stream:
            for choice in chunk.choices:
                delta = choice.delta.content
                if delta:
                    yield delta.encode("utf-8")

        yield b"\n\n--- End of review ---"