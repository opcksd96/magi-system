import os
import asyncio
from typing import Optional
from ollama import AsyncClient, ResponseError
from magi_core.providers.base import ModelProvider, MagiResponse


class OllamaProvider(ModelProvider):
    """
    Provider for local Ollama models.
    """

    def __init__(
        self,
        model: str = "llama3",
        cooldown_ms: int = 0,
        provider_name: str = "Ollama",
        base_url: str = "",
    ):
        super().__init__(cooldown_ms)
        self.model = model
        self.provider_name = provider_name
        # Fix for Windows: OLLAMA_HOST=0.0.0.0 works for binding but logic fails for client connection
        host = base_url or os.environ.get("OLLAMA_HOST", "")
        if "0.0.0.0" in host:
            host = "http://127.0.0.1:11434"

        self.client = AsyncClient(host=host if host else None)

    async def generate_raw(
        self, prompt: str, system_prompt: Optional[str] = None, **kwargs
    ) -> MagiResponse:
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        try:
            import time

            start_time = time.time()
            response = await self.client.chat(model=self.model, messages=messages)
            end_time = time.time()

            content = response["message"]["content"]
            usage = {
                "prompt_tokens": response.get("prompt_eval_count", 0),
                "completion_tokens": response.get("eval_count", 0),
                "total_tokens": response.get("prompt_eval_count", 0)
                + response.get("eval_count", 0),
            }
            return MagiResponse(
                content=content,
                model_name=self.model,
                provider_name=self.provider_name,
                token_usage=usage,
                raw_response=response,
                execution_time=end_time - start_time,
            )
        except ResponseError as e:
            raise RuntimeError(f"Ollama API Error: {e.error}") from e
        except Exception as e:  # noqa: BLE001
            # Wrap unexpected errors with context
            raise RuntimeError(f"Unexpected Ollama Provider Error: {str(e)}") from e

    async def health_check(self) -> bool:
        """
        System health check. Returns True if Ollama service is reachable.
        """
        try:
            await self.client.list()
            return True
        except (ResponseError, ConnectionError, OSError, asyncio.TimeoutError):
            # Known failure modes: API error, connection refused, or timeout
            return False
