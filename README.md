# AI Chatbot Application

This repository contains a production-ready AI chatbot with a React frontend and a FastAPI backend. It supports streaming responses, per-session memory, markdown rendering, and configurable model providers.

## 1️⃣ Architecture Overview

- **Frontend**: React + Vite for a fast, modern chat UI with responsive layout.
- **Backend**: FastAPI for async streaming via Server-Sent Events (SSE).
- **Memory**: In-memory session store with a clear interface for swapping to a database.
- **Provider Layer**: OpenAI-compatible provider with a swappable factory.
- **Observability**: Basic token usage estimates and error handling surfaced to the UI.

## 2️⃣ Folder Structure

```
.
├── backend
│   ├── .env.example
│   ├── main.py
│   ├── requirements.txt
│   └── services
│       ├── llm_provider.py
│       ├── memory_store.py
│       ├── rate_limit.py
│       └── safety.py
├── frontend
│   ├── .env.example
│   ├── index.html
│   ├── package.json
│   ├── vite.config.js
│   └── src
│       ├── App.jsx
│       ├── main.jsx
│       ├── styles.css
│       ├── components
│       │   ├── ChatInput.jsx
│       │   ├── MessageList.jsx
│       │   └── TypingIndicator.jsx
│       └── hooks
│           └── useChat.js
└── README.md
```

## 3️⃣ Backend Code

All backend files are under `backend/` and fully runnable with FastAPI. Refer to:
- `backend/main.py` for API routes and SSE streaming.
- `backend/services/llm_provider.py` for the provider abstraction.
- `backend/services/memory_store.py` for session memory.
- `backend/services/safety.py` and `backend/services/rate_limit.py` for stubs.

## 4️⃣ Frontend Code

All frontend files are under `frontend/` using React and Vite. Refer to:
- `frontend/src/App.jsx` for the UI shell.
- `frontend/src/hooks/useChat.js` for streaming logic.
- `frontend/src/components` for modular UI components.

## 5️⃣ Environment Setup

1. Copy environment templates:

```bash
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env
```

2. Fill in `LLM_API_KEY` and other settings in `backend/.env`.

## 6️⃣ Dependency Install

Backend:
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Frontend:
```bash
cd frontend
npm install
```

## 7️⃣ Run Instructions

Backend:
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Frontend:
```bash
cd frontend
npm run dev
```

Open `http://localhost:5173` in your browser.

## 8️⃣ Deployment Guide

- **Backend**: Deploy with Docker or a managed platform (Render, Fly.io). Use `uvicorn main:app --host 0.0.0.0 --port 8000`.
- **Frontend**: Build with `npm run build` and deploy `dist/` to Vercel, Netlify, or a static host.
- Ensure `VITE_API_BASE_URL` points to the backend URL.

## 9️⃣ Config Customization Guide

Adjust these in `backend/.env`:
- `LLM_PROVIDER`: switch to other OpenAI-compatible providers.
- `LLM_BASE_URL`: point to alternate model endpoints.
- `LLM_MODEL`: set your model name.
- `LLM_TEMPERATURE`: response creativity.
- `LLM_SYSTEM_PROMPT`: default system prompt.
- `RATE_LIMIT_REQUESTS` / `RATE_LIMIT_WINDOW_SECONDS`: in-memory rate limiting settings.
- `CORS_ORIGINS`: comma-separated list of allowed frontend origins.

## 🔟 Future Upgrade Options

- Add database-backed memory (PostgreSQL + SQLAlchemy).
- Add user authentication with JWT.
- Integrate rate limiting with Redis.
- Add message analytics and observability (OpenTelemetry).
- Support image or tool calls based on provider capabilities.
