import json
import httpx
from typing import AsyncGenerator, Dict, Any, Optional
from app.providers.base import BaseProvider

class AnthropicProvider(BaseProvider):
    def __init__(self, api_key: str, anthropic_version: str = "2023-06-01"):
        self.api_key = api_key
        self.base_url = "https://api.anthropic.com/v1"
        self.headers = {
            "x-api-key": self.api_key,
            "anthropic-version": anthropic_version,
            "content-type": "application/json"
        }

    async def generate(
        self, model: str, messages: list[Dict[str, str]], temperature: float, max_tokens: Optional[int] = 1024
    ) -> Dict[str, Any]:
        
        # Anthropic requires system prompts to be extracted from the messages array
        system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
        chat_messages = [m for m in messages if m["role"] != "system"]

        payload = {
            "model": model,
            "messages": chat_messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 1024,
            "stream": False
        }
        if system_msg:
            payload["system"] = system_msg

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/messages",
                json=payload,
                headers=self.headers,
                timeout=30.0
            )
            response.raise_for_status()
            data = response.json()
            
            # Normalize Anthropic's response to match the standard OpenAI format!
            return {
                "id": data["id"],
                "model": model,
                "content": data["content"][0]["text"],
                "usage": {
                    "prompt_tokens": data["usage"]["input_tokens"],
                    "completion_tokens": data["usage"]["output_tokens"],
                    "total_tokens": data["usage"]["input_tokens"] + data["usage"]["output_tokens"]
                }
            }

    async def generate_stream(
        self, model: str, messages: list[Dict[str, str]], temperature: float, max_tokens: Optional[int] = 1024
    ) -> AsyncGenerator[str, None]:
        
        system_msg = next((m["content"] for m in messages if m["role"] == "system"), "")
        chat_messages = [m for m in messages if m["role"] != "system"]

        payload = {
            "model": model,
            "messages": chat_messages,
            "temperature": temperature,
            "max_tokens": max_tokens or 1024,
            "stream": True
        }
        if system_msg:
            payload["system"] = system_msg

        async with httpx.AsyncClient() as client:
            async with client.stream(
                "POST",
                f"{self.base_url}/messages",
                json=payload,
                headers=self.headers,
                timeout=30.0
            ) as response:
                response.raise_for_status()
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        clean_line = line[6:].strip()
                        try:
                            data = json.loads(clean_line)
                            # Extract the text chunks from Anthropic's specific stream format
                            if data.get("type") == "content_block_delta":
                                delta = data["delta"].get("text", "")
                                if delta:
                                    yield f"data: {json.dumps({'chunk': delta})}\n\n"
                        except json.JSONDecodeError:
                            continue