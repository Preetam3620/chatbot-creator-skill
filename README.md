# chatbot-creator-skill

A Claude Code skill that scaffolds a complete, multi-provider LLM chatbot web app from a single command. Drop it into any project folder, invoke the skill, and it writes 40+ files across a FastAPI backend and a React + TypeScript + Vite frontend, with user registration, login, multi-turn conversation history persisted in SQLite, and token-by-token streaming. Supports Claude (Anthropic), OpenAI, and Gemini as chat providers, switchable via environment variable.

---

## What it builds

- **User auth**: register, login, logout with JWT (HS256) and bcrypt password hashing
- **Multi-provider chat**: Claude (Anthropic), OpenAI, and Gemini; select per session
- **WebSocket streaming**: tokens stream to the browser as they arrive
- **Conversation persistence**: multi-turn history stored in SQLite via SQLAlchemy
- **Session management**: create, list, and switch between named chat sessions
- **REST + WebSocket API**: FastAPI backend with auto-generated OpenAPI docs at `/docs`

---

## Prerequisites

| Tool | Minimum version |
|------|----------------|
| Python | 3.11 |
| Node.js | 18 |
| npm | 9 |

You will also need at least one LLM provider API key (Anthropic, OpenAI, or Google Gemini).

---

## Usage

```bash
# 1. Copy the skill into your project folder
mkdir my-chatbot && cd my-chatbot
# (copy SKILL.md, references/, and scripts/ here)

# 2. Open Claude Code and invoke the skill
# If backend/ or frontend/ already exist, Claude will list the files
# that would be overwritten and ask for confirmation before proceeding.
```

After scaffolding, follow the printed startup instructions:

```
cd backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # add your SECRET_KEY and API key(s)
uvicorn app.main:app --reload --port 8000

cd ../frontend
npm install
cp .env.example .env
npm run dev
# App: http://localhost:5173
```

---

## Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+, FastAPI 0.104, SQLAlchemy 2.0, LangGraph ≥0.2, SQLite |
| Frontend | React 18, TypeScript 5, Vite 5, React Router v6 |
| Auth | JWT (PyJWT + HS256), bcrypt via passlib |
| Streaming | WebSocket (browser native + FastAPI WebSocket) |

---

## Customization

All tuneable values live in `.env` files, no edits to core logic needed:

| Variable | Where | Purpose |
|----------|-------|---------|
| `ANTHROPIC_API_KEY` | `backend/.env` | Enable Claude provider |
| `OPENAI_API_KEY` | `backend/.env` | Enable OpenAI provider |
| `GEMINI_API_KEY` | `backend/.env` | Enable Gemini provider |
| `DATABASE_URL` | `backend/.env` | SQLite path (default: `sqlite:///./chatbot.db`) |
| `SECRET_KEY` | `backend/.env` | JWT signing secret, generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `backend/.env` | Session lifetime (default: 480 min) |
| `CORS_ORIGINS` | `backend/.env` | Frontend origin (default: `http://localhost:5173`) |
| `VITE_API_URL` | `frontend/.env` | Backend base URL (default: `http://localhost:8000`) |

---

## This skill does NOT

- Deploy to any cloud provider (no Docker, no Heroku, no Fly.io config)
- Set up PostgreSQL or any other database, SQLite only out of the box
- Configure OAuth or social login (email/password only)
- Add rate limiting beyond the basic `slowapi` stub included in requirements
- Generate tests or CI/CD configuration

---

## Project structure

```
backend/
  app/
    main.py              ← FastAPI app, lifespan, CORS, routers
    config.py            ← pydantic-settings; reads .env
    database.py          ← SQLAlchemy engine, SessionLocal, get_db
    models/              ← User, ChatSession, ChatMessage
    schemas/             ← Pydantic request/response models
    api/                 ← /api/auth/* and /api/chat/* routers
    services/
      chat_graph.py      ← LangGraph graph, MemorySaver, stream_response()
    utils/
      security.py        ← JWT encode/decode, password hash/verify
  requirements.txt
  .env.example

frontend/
  src/
    api/                 ← Typed fetch wrappers (auth, chat, client)
    hooks/               ← useAuth, useChat
    pages/               ← Login, Register, Chat
    components/          ← ProtectedRoute, SessionList, MessageList, ChatInput, ProviderBadge
    types/               ← Shared TypeScript interfaces
    styles/
  package.json
  vite.config.ts
  tsconfig.json
  .env.example
```

---

## Skill structure

```
SKILL.md                    ← Skill instructions (this is what Claude reads)
references/
  backend-reference.md      ← Verbatim Python source for all backend files
  frontend-reference.md     ← Verbatim TypeScript/TSX source for all frontend files
  startup-instructions.md   ← Printed at the end of scaffolding
scripts/
  validate_scaffold.py      ← Confirms all 40+ expected files were created
```

> **Note:** `SKILL.md`, `references/`, and `scripts/` must be kept together, the skill reads from `references/` at build time and runs `scripts/validate_scaffold.py` at the end.
