import json
import httpx
from typing import AsyncGenerator, Dict, Any, Optional
from app.providers.base import BaseProvider

class OpenAIProvider(BaseProvider):
    def __init__(self, api_key: str, base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def _convert_messages(self, messages: list[Dict[str, str]]) -> list[Dict[str, str]]:
        # Map normalization if needed; OpenAI is our standard schema benchmark
        return messages

    async def generate(
        self, model: str, messages: list[Dict[str, str]], temperature: float, max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        payload = {
            "model": model,
            "messages": self._convert_messages(messages),
            "temperature": temperature,
            "stream": False
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            # Normalize response payload format
            return {
                "id": data["id"],
                "model": data["model"],
                "content": data["choices"][0]["message"]["content"],
                "usage": {
                    "prompt_tokens": data["usage"]["prompt_tokens"],
                    "completion_tokens": data["usage"]["completion_tokens"],
                    "total_tokens": data["usage"]["total_tokens"]
                }
            }

    async def generate_stream(
        self, model: str, messages: list[Dict[str, str]], temperature: float, max_tokens: Optional[int] = None
    ) -> AsyncGenerator[str, None]:
        payload = {
            "model": model,
            "messages": self._convert_messages(messages),
            "temperature": temperature,
            "stream": True
        }
        if max_tokens:
            payload["max_tokens"] = max_tokens

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=self.headers,
                timeout=30.0
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        clean_line = line[6:].strip()
                        if clean_line == "[DONE]":
                            break
                        try:
                            data = json.loads(clean_line)
                            delta = data["choices"][0]["delta"].get("content", "")
                            if delta:
                                # Standardized SSE payload format for client consumption
                                yield f"data: {json.dumps({'chunk': delta})}\n\n"
                        except json.JSONDecodeError:
                            continue