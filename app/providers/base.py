from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Any, Optional

class BaseProvider(ABC):
    """
    Abstract Base Class for all LLM providers.
    Ensures absolute uniformity across different API signatures.
    """
    
    @abstractmethod
    async def generate(
        self, 
        model: str, 
        messages: list[Dict[str, str]], 
        temperature: float,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Handles non-streaming requests."""
        pass

    @abstractmethod
    async def generate_stream(
        self, 
        model: str, 
        messages: list[Dict[str, str]], 
        temperature: float,
        max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        """Handles streaming requests using Server-Sent Events (SSE)."""
        pass