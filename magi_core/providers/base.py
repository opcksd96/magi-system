import time
import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any

# Global throttler to prevent API BANs
_PROVIDER_LOCK = asyncio.Lock()
_LAST_REQUEST_TIME = 0.0


@dataclass
class MagiResponse:
    # ... (rest same as before) ...
    content: str
    model_name: str
    provider_name: str
    thinking_process: Optional[str] = None
    token_usage: Optional[Dict[str, int]] = None
    raw_response: Optional[Any] = None
    execution_time: float = 0.0


class ModelProvider(ABC):
    """Abstract base class for all MAGI model providers."""

    def __init__(self, cooldown_ms: int = 0):
        self.cooldown_ms = cooldown_ms

    async def _throttle(self):
        """Ensures that requests don't exceed the configured rate."""
        if self.cooldown_ms <= 0:
            return

        global _LAST_REQUEST_TIME
        async with _PROVIDER_LOCK:
            now = time.time()
            elapsed = (now - _LAST_REQUEST_TIME) * 1000
            if elapsed < self.cooldown_ms:
                wait_time = (self.cooldown_ms - elapsed) / 1000
                await asyncio.sleep(wait_time)
            _LAST_REQUEST_TIME = time.time()

    @abstractmethod
    async def generate_raw(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> MagiResponse:
        """Internal generation logic to be implemented by child classes."""
        pass

    async def generate(
        self, prompt: str, system_prompt: Optional[str] = None, **kwargs
    ) -> MagiResponse:
        """Wrapper that includes rate limiting (throttle)."""
        await self._throttle()
        return await self.generate_raw(prompt, system_prompt, **kwargs)

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is available and healthy."""
        pass
