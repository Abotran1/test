from __future__ import annotations

import json
from dataclasses import dataclass
from typing import AsyncGenerator, List, Optional

import httpx


@dataclass
class ChatMessage:
    role: str
    content: str


class LLMProviderError(Exception):
    pass


class OpenAIProvider:
    def __init__(self, api_key: str, base_url: str, model: str, temperature: float) -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.temperature = temperature

    async def stream_chat(
        self,
        messages: List[ChatMessage],
        system_prompt: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        if not self.api_key:
            raise LLMProviderError("LLM_API_KEY is not configured.")

        payload_messages = []
        if system_prompt:
            payload_messages.append({"role": "system", "content": system_prompt})
        payload_messages.extend([{"role": m.role, "content": m.content} for m in messages])

        payload = {
            "model": self.model,
            "messages": payload_messages,
            "temperature": self.temperature,
            "stream": True,
        }

        headers = {"Authorization": f"Bearer {self.api_key}"}
        url = f"{self.base_url}/chat/completions"

        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                if response.status_code >= 400:
                    detail = await response.aread()
                    raise LLMProviderError(
                        f"Provider error {response.status_code}: {detail.decode('utf-8')}"
                    )
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line.replace("data:", "").strip()
                    if data == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    delta = chunk.get("choices", [{}])[0].get("delta", {})
                    content = delta.get("content")
                    if content:
                        yield content


class LLMProviderFactory:
    def __init__(self, provider_name: str, api_key: str, base_url: str, model: str, temperature: float) -> None:
        self.provider_name = provider_name
        self.api_key = api_key
        self.base_url = base_url
        self.model = model
        self.temperature = temperature

    def create(self) -> OpenAIProvider:
        if self.provider_name.lower() != "openai":
            raise LLMProviderError(f"Unsupported provider: {self.provider_name}")
        return OpenAIProvider(
            api_key=self.api_key,
            base_url=self.base_url,
            model=self.model,
            temperature=self.temperature,
        )
