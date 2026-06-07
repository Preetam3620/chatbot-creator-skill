---
title: Chatbot Creator
emoji: 🤖
colorFrom: purple
colorTo: indigo
sdk: docker
pinned: false
license: mit
---

# Chatbot Creator

A full-stack LLM chatbot web application with user authentication, multi-turn conversation history, and real-time token streaming. Supports Claude (Anthropic), OpenAI, and Google Gemini as chat providers — switchable per session.

## Features

- **Multi-LLM support** — chat with Claude, OpenAI GPT, or Google Gemini; each session picks its own provider
- **User authentication** — register and login with JWT (HS256) and bcrypt password hashing
- **WebSocket streaming** — tokens stream to the browser as the model generates them
- **LangGraph memory** — multi-turn conversation context managed by LangGraph MemorySaver
- **Session management** — create, list, rename, and switch between multiple chat sessions
- **REST + WebSocket API** — FastAPI backend with auto-generated OpenAPI docs at `/docs`

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11, FastAPI 0.104, SQLAlchemy 2.0, LangGraph ≥0.2, SQLite |
| Frontend | React 18, TypeScript 5, Vite 5, React Router v6 |
| Auth | JWT (PyJWT HS256), bcrypt via passlib |
| Streaming | WebSocket (FastAPI native) |

## Required Environment Variables

Set these as **Space secrets** before the app will work:

| Variable | Required | Description |
|----------|----------|-------------|
| `SECRET_KEY` | **Yes** | JWT signing secret — generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `ANTHROPIC_API_KEY` | If using Claude | Your Anthropic API key |
| `OPENAI_API_KEY` | If using OpenAI | Your OpenAI API key |
| `GEMINI_API_KEY` | If using Gemini | Your Google Gemini API key |

You need at least one LLM provider API key for the app to answer messages.

## How to Set Secrets on HuggingFace

1. Open your Space on HuggingFace
2. Click **Settings** → **Variables and secrets**
3. Under **Repository secrets**, click **New secret**
4. Add `SECRET_KEY` and whichever API key(s) you want to enable

## Database Note

`DATABASE_URL` defaults to `sqlite:///./chatbot.db`. This is fine for demos, but the database **resets on every container restart** because HuggingFace Spaces use ephemeral storage. For durable storage, set `DATABASE_URL` to a remote database connection string (e.g. PostgreSQL).

## Local Development

After scaffolding with the chatbot-creator skill:

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
cp .env.example .env         # fill in SECRET_KEY and at least one API key
uvicorn app.main:app --reload --port 8000

# Frontend (separate terminal)
cd frontend
npm install
cp .env.example .env         # set VITE_API_URL=http://localhost:8000
npm run dev
# App: http://localhost:5173
```
