from __future__ import annotations

import json
import os
from typing import AsyncGenerator, List

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from services.llm_provider import ChatMessage, LLMProviderError, LLMProviderFactory
from services.memory_store import MemoryStore
from services.rate_limit import RateLimiter
from services.safety import SafetyFilter

load_dotenv()

APP_ENV = os.getenv("APP_ENV", "development")
APP_HOST = os.getenv("APP_HOST", "0.0.0.0")
APP_PORT = int(os.getenv("APP_PORT", "8000"))

LLM_PROVIDER = os.getenv("LLM_PROVIDER", "openai")
LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.openai.com/v1")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.2"))
LLM_SYSTEM_PROMPT = os.getenv("LLM_SYSTEM_PROMPT", "You are a helpful assistant.")
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "30"))
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "60"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

app = FastAPI(title="AI Chatbot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in CORS_ORIGINS if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

memory_store = MemoryStore(max_history_messages=MAX_HISTORY_MESSAGES)
rate_limiter = RateLimiter(max_requests=RATE_LIMIT_REQUESTS, window_seconds=RATE_LIMIT_WINDOW_SECONDS)
safety_filter = SafetyFilter()


class SessionResponse(BaseModel):
    session_id: str


class ChatRequest(BaseModel):
    session_id: str
    message: str = Field(..., min_length=1)
    system_prompt: str | None = None
    temperature: float | None = None


class HistoryResponse(BaseModel):
    session_id: str
    messages: List[dict]


@app.get("/api/session", response_model=SessionResponse)
async def create_session() -> SessionResponse:
    session_id = memory_store.create_session()
    return SessionResponse(session_id=session_id)


@app.get("/api/health")
async def health_check() -> dict:
    return {"status": "ok", "environment": APP_ENV}


@app.get("/api/history/{session_id}", response_model=HistoryResponse)
async def get_history(session_id: str) -> HistoryResponse:
    messages = memory_store.get_messages(session_id)
    return HistoryResponse(
        session_id=session_id,
        messages=[{"role": m.role, "content": m.content, "timestamp": m.timestamp} for m in messages],
    )


@app.post("/api/reset/{session_id}")
async def reset_session(session_id: str) -> dict:
    memory_store.reset_session(session_id)
    return {"status": "ok"}


@app.post("/api/chat/stream")
async def stream_chat(request: Request, payload: ChatRequest) -> StreamingResponse:
    client_ip = request.client.host if request.client else "unknown"
    rate_status = rate_limiter.check(client_ip)
    if not rate_status.allowed:
        raise HTTPException(status_code=429, detail="Rate limit exceeded.")

    ok, reason = safety_filter.check(payload.message)
    if not ok:
        raise HTTPException(status_code=400, detail=reason)

    messages = memory_store.get_messages(payload.session_id)
    user_message = ChatMessage(role="user", content=payload.message)
    memory_store.append_message(payload.session_id, user_message.role, user_message.content)

    model_messages = [ChatMessage(role=m.role, content=m.content) for m in messages] + [user_message]

    provider = LLMProviderFactory(
        provider_name=LLM_PROVIDER,
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        model=LLM_MODEL,
        temperature=payload.temperature if payload.temperature is not None else LLM_TEMPERATURE,
    ).create()

    async def event_stream() -> AsyncGenerator[str, None]:
        assistant_content = ""
        try:
            async for chunk in provider.stream_chat(
                model_messages,
                system_prompt=payload.system_prompt or LLM_SYSTEM_PROMPT,
            ):
                assistant_content += chunk
                yield _format_sse({"type": "chunk", "content": chunk})
        except LLMProviderError as exc:
            yield _format_sse({"type": "error", "message": str(exc)})
            return
        except Exception as exc:  # pragma: no cover - safeguard
            yield _format_sse({"type": "error", "message": f"Unexpected error: {exc}"})
            return

        if assistant_content:
            memory_store.append_message(payload.session_id, "assistant", assistant_content)

        usage = {
            "approx_input_tokens": _approx_token_count(payload.message),
            "approx_output_tokens": _approx_token_count(assistant_content),
        }
        yield _format_sse({"type": "end", "usage": usage})

    headers = {
        "Cache-Control": "no-cache",
        "Connection": "keep-alive",
        "X-Accel-Buffering": "no",
    }
    return StreamingResponse(event_stream(), media_type="text/event-stream", headers=headers)


def _format_sse(data: dict) -> str:
    return f"data: {json.dumps(data)}\n\n"


def _approx_token_count(text: str) -> int:
    return max(1, len(text.split()))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host=APP_HOST, port=APP_PORT, reload=APP_ENV == "development")
