---
name: chatbot-creator-skill
description: Scaffold a standalone LLM chatbot app (FastAPI + React + Vite). Builds the full project — user auth, multi-turn chat with Claude/OpenAI/Gemini, WebSocket streaming, SQLite persistence. Warns before overwriting existing files.
---

# Chatbot Creator

You are building a complete, standalone LLM chatbot application from scratch.

**Reference files:** All verbatim file contents live in `references/`. Read each reference file once at the step that needs it — do not re-read on every file write.

> **Required structure:** `SKILL.md`, `references/`, and `scripts/` must exist in the same directory. The skill reads from `references/` at build time and runs `scripts/validate_scaffold.py` at the end.

---

## When to Invoke

Invoke this skill when the user asks to:
- "build me a chatbot" / "create a chat app" / "make a chatbot application"
- "scaffold a chatbot" / "new chatbot project" / "set up a chat app from scratch"
- Any request to create a full-stack LLM chat application with a FastAPI backend and React frontend

Do **not** invoke for:
- Adding chat features to an existing app
- Modifying or extending an already-scaffolded chatbot project
- General LLM API questions without a build request

---

## This Skill Does NOT

- Deploy to any cloud provider — no Docker, Heroku, or Fly.io config
- Configure PostgreSQL or any other database — SQLite only out of the box
- Set up OAuth or social login — email/password auth only
- Generate tests or CI/CD pipelines
- Modify or extend an existing project's architecture

---

## Stack & Versions

| Layer | Technology |
|-------|------------|
| Backend | Python 3.11+, FastAPI 0.104, SQLAlchemy 2.0, LangGraph ≥0.2, SQLite (default) |
| Frontend | React 18, TypeScript 5, Vite 5, React Router v6 |
| Auth | JWT (PyJWT + HS256), bcrypt password hashing |
| Streaming | WebSocket (browser native + FastAPI WebSocket) |

---

## Project Structure

```
backend/
  app/
    __init__.py
    main.py              ← FastAPI app + lifespan + CORS + routers
    config.py            ← pydantic-settings; reads .env
    database.py          ← SQLAlchemy engine + SessionLocal + get_db
    models/
      __init__.py
      user.py
      chat.py
    schemas/
      __init__.py
      auth.py
      chat.py
    api/
      __init__.py
      auth.py            ← /api/auth/register, /login, /logout, /me
      chat.py            ← REST CRUD + WebSocket /api/chat/ws/{id}?token=<jwt>
    services/
      __init__.py
      chat_graph.py      ← LangGraph: MemorySaver, build_graph(), stream_response()
    utils/
      __init__.py
      security.py        ← JWT encode/decode, password hash/verify, revocation
  requirements.txt
  .env.example

frontend/
  src/
    main.tsx
    App.tsx
    api/
      client.ts
      auth.ts
      chat.ts
    hooks/
      useAuth.ts
      useChat.ts
    pages/
      Login.tsx
      Register.tsx
      Chat.tsx
    components/
      ProtectedRoute.tsx
      SessionList.tsx
      MessageList.tsx
      ChatInput.tsx
      ProviderBadge.tsx
    types/
      index.ts
    styles/
      index.css
  package.json
  vite.config.ts
  tsconfig.json
  .env.example
```

---

## Build Steps

### Step 1 — Backend config files

**Before writing any files**, check whether `backend/` or `frontend/` directories already exist in the current working directory. If either exists, list every file from `scripts/validate_scaffold.py`'s `EXPECTED_FILES` that is already present, then print:

```
⚠️  The following files already exist and will be overwritten:
  <list each existing file, one per line>

Type "yes" to continue and overwrite, or anything else to abort.
```

Wait for the user's response. Proceed only if they type exactly "yes". Otherwise stop immediately.

---

**Read `references/backend-reference.md` now** (once — keep it in context for all of Step 2).

Create `backend/requirements.txt` and `backend/.env.example` — copy verbatim from Backend Reference.

### Step 2 — Backend Python files (dependency order)

Files marked ✦ are copied verbatim from `references/backend-reference.md`. Files without ✦ are either empty or have a one-line description that is sufficient to generate them correctly.

1. `backend/app/__init__.py` — empty file
2. `backend/app/config.py` ✦
3. `backend/app/database.py` ✦
4. `backend/app/models/__init__.py` — imports User, ChatSession, ChatMessage
5. `backend/app/models/user.py` ✦
6. `backend/app/models/chat.py` ✦
7. `backend/app/schemas/__init__.py` — empty
8. `backend/app/schemas/auth.py` ✦
9. `backend/app/schemas/chat.py` ✦
10. `backend/app/utils/__init__.py` — empty
11. `backend/app/utils/security.py` ✦
12. `backend/app/services/__init__.py` — empty
13. `backend/app/services/chat_graph.py` ✦
14. `backend/app/api/__init__.py` — empty
15. `backend/app/api/auth.py` ✦
16. `backend/app/api/chat.py` ✦
17. `backend/app/main.py` ✦

> ⚠️ **Common pitfalls**
> - **Windows venv**: use `venv\Scripts\activate`, not `source venv/bin/activate`
> - **Python version**: confirm `python --version` shows 3.11+ before creating the venv
> - **Port conflict**: if port 8000 is taken, change the uvicorn command and update `CORS_ORIGINS` in `.env` to match
> - **WebSocket auth**: the token travels as a query string (`?token=<jwt>`); some reverse proxies strip query strings — note this if the user deploys behind nginx or Caddy

### Step 3 — Frontend config files

**Read `references/frontend-reference.md` now** (once — keep in context for all of Step 4).

Create `frontend/package.json`, `frontend/vite.config.ts`, `frontend/tsconfig.json`, `frontend/tsconfig.node.json`, `frontend/.env.example` — copy verbatim from Frontend Reference.

Also create `frontend/index.html` — standard Vite HTML shell with `<div id="root">` and `<script type="module" src="/src/main.tsx">`.

### Step 4 — Frontend TypeScript/TSX files (dependency order)

All files in this step are copied verbatim from `references/frontend-reference.md`.

1. `frontend/src/types/index.ts`
2. `frontend/src/api/client.ts`
3. `frontend/src/api/auth.ts`
4. `frontend/src/api/chat.ts`
5. `frontend/src/hooks/useAuth.ts`
6. `frontend/src/hooks/useChat.ts`
7. `frontend/src/components/ProtectedRoute.tsx`
8. `frontend/src/components/ProviderBadge.tsx`
9. `frontend/src/components/SessionList.tsx`
10. `frontend/src/components/MessageList.tsx`
11. `frontend/src/components/ChatInput.tsx`
12. `frontend/src/pages/Login.tsx`
13. `frontend/src/pages/Register.tsx`
14. `frontend/src/pages/Chat.tsx`
15. `frontend/src/App.tsx`
16. `frontend/src/main.tsx`
17. `frontend/src/styles/index.css`

> ⚠️ **TypeScript check**: After all frontend files are written, run `npm run build` in `frontend/` to confirm zero TypeScript errors before the user customizes anything.

### Step 5 — Validate and print startup instructions

Run the validation script to confirm all files were created:

```
python scripts/validate_scaffold.py
```

If any files are missing, re-run the relevant build step before continuing. Once all files are present, read `references/startup-instructions.md` and print its contents exactly as written.
