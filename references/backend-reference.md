# Backend Reference

Verbatim file contents for all backend files. Copy exactly as shown — do not paraphrase or restructure.

---

## `backend/requirements.txt`

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
pydantic[email]==2.5.0
pydantic-settings==2.1.0
PyJWT[crypto]>=2.8.0
argon2-cffi>=23.1.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
cryptography>=43.0.0
langgraph>=0.2.0
langchain-core>=0.3.0
langchain-anthropic>=0.3.0
langchain-openai>=0.2.0
langchain-google-genai>=2.0.0
slowapi>=0.1.9
```

---

## `backend/.env.example`

```
DATABASE_URL=sqlite:///./chatbot.db
SECRET_KEY=change-me-generate-with-python-secrets.token_urlsafe-32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=480
CORS_ORIGINS=http://localhost:5173
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GEMINI_API_KEY=
```

---

## `backend/app/config.py`

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./chatbot.db"
    SECRET_KEY: str = "change-me-generate-with-python-secrets.token_urlsafe-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480
    CORS_ORIGINS: str = "http://localhost:5173"
    ANTHROPIC_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
```

---

## `backend/app/database.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## `backend/app/models/user.py`

```python
from sqlalchemy import Column, Integer, String, Text
from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(Text, nullable=False)
    anthropic_api_key = Column(Text, nullable=True)
    openai_api_key = Column(Text, nullable=True)
    gemini_api_key = Column(Text, nullable=True)
```

---

## `backend/app/models/chat.py`

```python
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(60), nullable=True)
    llm_provider = Column(String(20), nullable=False)
    llm_model = Column(String(80), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc),
                        onupdate=lambda: datetime.now(timezone.utc))

    messages = relationship("ChatMessage", back_populates="session",
                            cascade="all, delete-orphan", lazy="select")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"),
                        nullable=False, index=True)
    role = Column(String(10), nullable=False)   # "user" | "assistant"
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    session = relationship("ChatSession", back_populates="messages")
```

---

## `backend/app/schemas/auth.py`

```python
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    email: str

    model_config = {"from_attributes": True}
```

---

## `backend/app/schemas/chat.py`

```python
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, field_validator

VALID_PROVIDERS = {"claude", "openai", "gemini"}


class ChatSessionCreate(BaseModel):
    llm_provider: str
    llm_model: Optional[str] = None

    @field_validator("llm_provider")
    @classmethod
    def validate_provider(cls, v: str) -> str:
        if v not in VALID_PROVIDERS:
            raise ValueError(f"llm_provider must be one of {VALID_PROVIDERS}")
        return v


class ChatMessageRequest(BaseModel):
    message: str
    llm_provider: Optional[str] = None
    llm_model: Optional[str] = None

    @field_validator("message")
    @classmethod
    def validate_message(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("message cannot be empty")
        if len(v) > 3000:
            raise ValueError("message too long (max 3000 chars)")
        return v


class ChatSessionResponse(BaseModel):
    id: int
    title: Optional[str]
    llm_provider: str
    llm_model: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatHistoryResponse(BaseModel):
    session: ChatSessionResponse
    messages: List[ChatMessageResponse]
```

---

## `backend/app/utils/security.py`

```python
import jwt
from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory revocation set — cleared on server restart
_revoked_jtis: set[str] = set()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(data: dict) -> str:
    payload = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload.update({"exp": expire})
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.PyJWTError:
        return None


def revoke_token(jti: str) -> None:
    _revoked_jtis.add(jti)


def is_token_revoked(jti: str) -> bool:
    return jti in _revoked_jtis
```

---

## `backend/app/services/chat_graph.py`

```python
import os
from typing import AsyncGenerator
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, START, END, MessagesState
from langgraph.checkpoint.memory import MemorySaver
from app.config import settings

# ── Shared in-process memory ──────────────────────────────────────────────────

_memory = MemorySaver()

# Noop graph — no LLM node. Used only to read/write the shared checkpointer
# without instantiating any LLM client. Lets us call aget_state / aupdate_state
# for memory seeding without paying the cost of building a real graph.
def _noop(state: MessagesState) -> dict:
    return {}

_seed_builder = StateGraph(MessagesState)
_seed_builder.add_node("noop", _noop)
_seed_builder.add_edge(START, "noop")
_seed_builder.add_edge("noop", END)
_seed_graph = _seed_builder.compile(checkpointer=_memory)

# ── Provider defaults ─────────────────────────────────────────────────────────

_PROVIDER_DEFAULTS = {
    "claude": "claude-sonnet-4-6",
    "openai": "gpt-4o-mini",
    "gemini": "gemini-2.0-flash",
}

# ── Memory seeding helpers ────────────────────────────────────────────────────

async def is_thread_seeded(thread_id: str) -> bool:
    """Return True if _memory already has messages for this thread."""
    config = {"configurable": {"thread_id": thread_id}}
    state = await _seed_graph.aget_state(config)
    msgs = state.values.get("messages", []) if state and state.values else []
    return len(msgs) > 0


async def seed_memory_from_history(thread_id: str, db_messages: list) -> None:
    """Replay DB rows into the shared MemorySaver via the noop graph.
    Called once after a server restart when is_thread_seeded() returns False."""
    config = {"configurable": {"thread_id": thread_id}}
    lc_messages = []
    for m in db_messages:
        if m.role == "user":
            lc_messages.append(HumanMessage(content=m.content))
        else:
            lc_messages.append(AIMessage(content=m.content))
    if lc_messages:
        await _seed_graph.aupdate_state(config, {"messages": lc_messages})

# ── API key resolution ────────────────────────────────────────────────────────

def _resolve_key(user_key: str | None, env_var: str) -> str:
    """User-stored key wins; fall back to environment variable."""
    return user_key or getattr(settings, env_var, "") or ""

# ── Graph builder ─────────────────────────────────────────────────────────────

def build_graph(provider: str, model: str | None, user_key: str | None = None):
    """Build a real LLM-backed StateGraph for the given provider."""
    model = model or _PROVIDER_DEFAULTS.get(provider, "")

    if provider == "claude":
        from langchain_anthropic import ChatAnthropic
        api_key = _resolve_key(user_key, "ANTHROPIC_API_KEY")
        llm = ChatAnthropic(model=model, api_key=api_key, streaming=True)
    elif provider == "openai":
        from langchain_openai import ChatOpenAI
        api_key = _resolve_key(user_key, "OPENAI_API_KEY")
        llm = ChatOpenAI(model=model, api_key=api_key, streaming=True)
    elif provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        api_key = _resolve_key(user_key, "GEMINI_API_KEY")
        llm = ChatGoogleGenerativeAI(model=model, google_api_key=api_key)
    else:
        raise ValueError(f"Unknown provider: {provider}")

    system_msg = SystemMessage(content="You are a helpful AI assistant.")

    async def chat_node(state: MessagesState) -> dict:
        messages = [system_msg] + state["messages"]
        response = await llm.ainvoke(messages)
        return {"messages": [response]}

    builder = StateGraph(MessagesState)
    builder.add_node("chat", chat_node)
    builder.add_edge(START, "chat")
    builder.add_edge("chat", END)
    return builder.compile(checkpointer=_memory)

# ── Streaming ─────────────────────────────────────────────────────────────────

async def stream_response(
    graph,
    user_message: str,
    thread_id: str,
) -> AsyncGenerator[str, None]:
    """Yield token strings from graph.astream_events (version v2)."""
    config = {"configurable": {"thread_id": thread_id}}
    input_state = {"messages": [HumanMessage(content=user_message)]}
    async for event in graph.astream_events(input_state, config=config, version="v2"):
        if event["event"] == "on_chat_model_stream":
            chunk = event["data"].get("chunk")
            if chunk and hasattr(chunk, "content") and chunk.content:
                yield chunk.content
```

---

## `backend/app/api/auth.py`

```python
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.schemas.auth import UserCreate, UserLogin, Token, UserResponse
from app.utils.security import (
    hash_password, verify_password, create_access_token,
    decode_access_token, revoke_token,
)

router = APIRouter(prefix="/api/auth", tags=["auth"])


def get_current_user(token: str = Depends(lambda: None), db: Session = Depends(get_db)) -> User:
    raise NotImplementedError  # overridden below via import


# ── Dependency injected by the router ────────────────────────────────────────

from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

_bearer = HTTPBearer()


def _get_user(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    payload = decode_access_token(creds.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.query(User).filter(User.id == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


@router.post("/register", response_model=UserResponse, status_code=201)
def register(body: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == body.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(email=body.email, hashed_password=hash_password(body.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=Token)
def login(body: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == body.email).first()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    jti = str(uuid.uuid4())
    token = create_access_token({"sub": user.id, "jti": jti})
    return {"access_token": token, "token_type": "bearer"}


@router.post("/logout", status_code=204)
def logout(
    creds: HTTPAuthorizationCredentials = Depends(_bearer),
):
    payload = decode_access_token(creds.credentials)
    if payload and (jti := payload.get("jti")):
        revoke_token(jti)


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(_get_user)):
    return user


# Re-export for use in chat router
get_current_user = _get_user
```

---

## `backend/app/api/chat.py`

```python
import json
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session, selectinload
from app.database import get_db
from app.models.user import User
from app.models.chat import ChatSession, ChatMessage
from app.schemas.chat import ChatSessionCreate, ChatSessionResponse, ChatHistoryResponse
from app.api.auth import get_current_user
from app.services.chat_graph import (
    build_graph, stream_response, is_thread_seeded, seed_memory_from_history,
)
from app.utils.security import decode_access_token, is_token_revoked

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["chat"])

_PROVIDER_KEY_FIELD = {
    "claude": "anthropic_api_key",
    "openai": "openai_api_key",
    "gemini": "gemini_api_key",
}


# ── REST endpoints ────────────────────────────────────────────────────────────

@router.post("/sessions", response_model=ChatSessionResponse, status_code=201)
def create_session(
    body: ChatSessionCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = ChatSession(
        user_id=user.id,
        llm_provider=body.llm_provider,
        llm_model=body.llm_model,
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


@router.get("/sessions", response_model=list[ChatSessionResponse])
def list_sessions(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return (
        db.query(ChatSession)
        .filter(ChatSession.user_id == user.id)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )


@router.get("/sessions/{session_id}", response_model=ChatHistoryResponse)
def get_session(
    session_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = (
        db.query(ChatSession)
        .options(selectinload(ChatSession.messages))
        .filter(ChatSession.id == session_id, ChatSession.user_id == user.id)
        .first()
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"session": session, "messages": session.messages}


@router.delete("/sessions/{session_id}", status_code=204)
def delete_session(
    session_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id, ChatSession.user_id == user.id
    ).first()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    db.delete(session)
    db.commit()


# ── WebSocket helpers ─────────────────────────────────────────────────────────

def _auth_ws(token: str, db: Session) -> User | None:
    payload = decode_access_token(token)
    if not payload:
        return None
    jti = payload.get("jti")
    if jti and is_token_revoked(jti):
        return None
    return db.query(User).filter(User.id == payload.get("sub")).first()


def _get_user_key(user: User, provider: str) -> str | None:
    field = _PROVIDER_KEY_FIELD.get(provider)
    return getattr(user, field, None) if field else None


# ── WebSocket endpoint ────────────────────────────────────────────────────────

@router.websocket("/ws/{session_id}")
async def ws_chat(
    websocket: WebSocket,
    session_id: int,
    token: str = "",
    db: Session = Depends(get_db),
):
    # Auth via query param (browser WS API cannot send custom headers)
    user = _auth_ws(token, db)
    if not user:
        await websocket.close(code=4001)
        return

    session = db.query(ChatSession).filter(
        ChatSession.id == session_id, ChatSession.user_id == user.id
    ).first()
    if not session:
        await websocket.close(code=4004)
        return

    await websocket.accept()

    thread_id = str(session_id)
    graph = None
    current_provider = None
    current_model = None

    # Seed memory once on connect (restores context after server restart)
    if not await is_thread_seeded(thread_id):
        history = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
            .all()
        )
        await seed_memory_from_history(thread_id, history)

    try:
        while True:
            raw = await websocket.receive_text()
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                await websocket.send_text(json.dumps({"type": "error", "detail": "Invalid JSON"}))
                continue

            user_text = (data.get("message") or "").strip()
            if not user_text:
                continue

            provider = data.get("llm_provider") or session.llm_provider
            model = data.get("llm_model") or session.llm_model

            # Rebuild graph only when provider or model changes
            if graph is None or provider != current_provider or model != current_model:
                user_key = _get_user_key(user, provider)
                try:
                    graph = build_graph(provider, model, user_key)
                    current_provider = provider
                    current_model = model
                except Exception as exc:
                    await websocket.send_text(json.dumps({"type": "error", "detail": str(exc)}))
                    continue

            # Persist user message
            user_msg = ChatMessage(session_id=session_id, role="user", content=user_text)
            db.add(user_msg)
            db.commit()

            # Auto-set title from first message
            if not session.title:
                session.title = user_text[:60]
                db.commit()

            # Stream response
            full_response = ""
            try:
                async for token_text in stream_response(graph, user_text, thread_id):
                    full_response += token_text
                    await websocket.send_text(json.dumps({"type": "token", "content": token_text}))
            except Exception as exc:
                logger.exception("Streaming error")
                await websocket.send_text(json.dumps({"type": "error", "detail": str(exc)}))
                continue

            # Persist assistant message
            assistant_msg = ChatMessage(session_id=session_id, role="assistant", content=full_response)
            db.add(assistant_msg)
            session.updated_at = datetime.now(timezone.utc)
            db.commit()

            await websocket.send_text(json.dumps({"type": "done"}))

    except WebSocketDisconnect:
        pass
```

---

## `backend/app/main.py`

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
import app.models.user  # noqa: F401 — register ORM models
import app.models.chat  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title="Chatbot API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from app.api import auth, chat  # noqa: E402
app.include_router(auth.router)
app.include_router(chat.router)
```
