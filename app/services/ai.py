from typing import List, Union, AsyncGenerator, cast
from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletionSystemMessageParam,
    ChatCompletionUserMessageParam,
)
from app.schemas.submissions import SubmissionCreate
from app.schemas.ai import ReviewPayload
from openai import RateLimitError, APIError, APIConnectionError


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

    def build_messages(
        self, data: SubmissionCreate | ReviewPayload
    ) -> List[Union[ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam]]:
        prompt_text = (
            f"Act as a senior backend engineer. "
            f"Analyze this {data.language} code for backend issues. "
            "Format response as:\n\n"
            "1. Brief summary (1 sentence)\n"
            "2. Key findings (bulleted list)\n"
            "3. Most critical recommendation\n"
            "Avoid markdown. Be technical but concise."
        )
        code_input = data.payload.model_dump()
        if "content" not in code_input:
            raise Exception("Missing code to review.")
        messages: List[
            Union[ChatCompletionSystemMessageParam, ChatCompletionUserMessageParam]
        ] = [
            cast(
                ChatCompletionSystemMessageParam,
                {"role": "system", "content": self.TECHNICAL_PERSONA},
            ),
            cast(
                ChatCompletionUserMessageParam,
                {
                    "role": "user",
                    "content": f"{prompt_text}\n\n{code_input['content']}",
                },
            ),
        ]

        return messages

    async def get_feedback(self, data: SubmissionCreate | ReviewPayload) -> str | None:
        messages = self.build_messages(data)

        try:
            chat = await self.ai_client.chat.completions.create(
                model=self.OPENAI_MODEL,
                messages=messages,
            )
            return chat.choices[0].message.content

        except RateLimitError:
            return "Too many requests. Please try again later."

        except APIConnectionError:
            return "Could not reach the AI service."

        except APIError as e:
            return f"AI service error: {e}"

        except Exception as e:
            print(f"Unexpected error in get_feedback: {e}")
            return None

    async def stream_feedback(
        self, data: SubmissionCreate | ReviewPayload
    ) -> AsyncGenerator[bytes, None]:
        messages = self.build_messages(data)

        try:
            stream = await self.ai_client.chat.completions.create(
                model=self.OPENAI_MODEL,
                messages=messages,
                stream=True,
            )

            async for chunk in stream:
                for choice in chunk.choices:
                    delta = choice.delta.content
                    if delta:
                        yield delta.encode("utf-8")

        except RateLimitError:
            yield b"Too many requests. Please try again later."

        except APIConnectionError:
            yield b"Could not reach the AI service."

        except APIError as e:
            yield f"AI service error: {e}".encode("utf-8")

        except Exception as e:
            print(f"Unexpected error in stream_feedback: {e}")
            yield b"Unexpected error occurred."
