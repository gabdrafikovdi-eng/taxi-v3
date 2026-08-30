# app/llm/client.py

import logging

from openai import APIError, APITimeoutError, AsyncOpenAI
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from app.core.config import config_settings

logger = logging.getLogger(__name__)


class LLMClient:
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> None:
        self.max_retries = config_settings.MAX_RETRIES_LLM_CLIENT
        self.timeout = config_settings.TIMEOUT_LLM
        self.OPENAI_API_KEY = config_settings.OPENAI_API_KEY
        self.OPENAI_BASE_URL = config_settings.OPENAI_BASE_URL
        self.OPENAI_MODEL = config_settings.OPENAI_MODEL
        self._client = AsyncOpenAI(
            api_key=self.OPENAI_API_KEY or api_key,
            base_url=self.OPENAI_BASE_URL or base_url,
            timeout=self.timeout,
            max_retries=self.max_retries,
        )
        self._model = self.OPENAI_MODEL or model

    async def chat(
        self,
        messages: list[dict],
        tools: list[dict] | None = None,
    ) -> ChatCompletionMessage | None:
        try:
            kwargs: dict = {
                "model": self._model,
                "messages": messages,
            }
            if tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            response = await self._client.chat.completions.create(**kwargs)
            return response.choices[0].message
        except (APIError, APITimeoutError) as e:
            logger.error("LLM request failed: %s", e)
            return None
