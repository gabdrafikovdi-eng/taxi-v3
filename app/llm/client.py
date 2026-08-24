# app/llm/client.py
import os
from openai import AsyncOpenAI
from app.core.config import config_settings


class LLMClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self._client = AsyncOpenAI(
            api_key=config_settings.OPENAI_API_KEY,
            base_url=config_settings.OPENAI_BASE_URL,
        )
        self._model = config_settings.OPENAI_MODEL

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> dict:
        kwargs: dict = {
            "model": self._model,
            "messages": messages,
        }

        if tools:
            kwargs["tools"] = tools
            kwargs["tool_choice"] = "auto"

        response = await self._client.chat.completions.create(**kwargs)
        return response.choices[0].message
