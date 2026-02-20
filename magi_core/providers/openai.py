import os
from typing import Optional, Dict, Any
from openai import AsyncOpenAI
from .base import ModelProvider, MagiResponse


class OpenAIProvider(ModelProvider):
    """
    Provider for OpenAI API (GPT-4o, GPT-3.5-turbo).
    """

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required.")

        self.client = AsyncOpenAI(api_key=self.api_key)
        self.model = model

    async def generate(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> MagiResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        try:
            response = await self.client.chat.completions.create(
                model=self.model, messages=messages
            )

            content = response.choices[0].message.content

            usage = None
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            return MagiResponse(
                content=content,
                model_name=self.model,
                provider_name="OpenAI",
                token_usage=usage,
                raw_response=response.model_dump(),
            )
        except Exception as e:
            # MAGI should gracefully fail or retry, but for now raise
            # Encapsulate in a custom exception if needed
            raise RuntimeError(f"OpenAI API Error: {str(e)}")

    async def health_check(self) -> bool:
        try:
            # Simple models list check
            await self.client.models.list()
            return True
        except Exception:
            return False
