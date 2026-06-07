# Frontend Reference

Verbatim file contents for all frontend files. Copy exactly as shown — do not paraphrase or restructure.

---

## `frontend/package.json`

```json
{
  "name": "chatbot-frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "lint": "eslint src --ext ts,tsx",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.22.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@typescript-eslint/eslint-plugin": "^7.0.0",
    "@typescript-eslint/parser": "^7.0.0",
    "@vitejs/plugin-react": "^4.2.0",
    "eslint": "^8.57.0",
    "typescript": "^5.3.0",
    "vite": "^5.1.0"
  }
}
```

---

## `frontend/vite.config.ts`

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
});
```

---

## `frontend/tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

---

## `frontend/tsconfig.node.json`

```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

---

## `frontend/.env.example`

```
VITE_API_URL=http://localhost:8000
```

---

## `frontend/src/types/index.ts`

```typescript
export interface User {
  id: number;
  email: string;
}

export interface Session {
  id: number;
  title: string | null;
  llm_provider: string;
  llm_model: string | null;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  streaming?: boolean;
}
```

---

## `frontend/src/api/client.ts`

```typescript
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export async function request<T>(
  path: string,
  options: RequestInit = {},
): Promise<{ data?: T; error?: string }> {
  const token = localStorage.getItem('auth_token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> | undefined),
  };
  if (token) headers['Authorization'] = `Bearer ${token}`;

  try {
    const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
    if (res.status === 204) return {};
    const body = await res.json();
    if (!res.ok) return { error: body.detail || res.statusText };
    return { data: body as T };
  } catch (err) {
    return { error: err instanceof Error ? err.message : 'Network error' };
  }
}
```

---

## `frontend/src/api/auth.ts`

```typescript
import { request } from './client';
import type { User } from '../types';

export const login = (email: string, password: string) =>
  request<{ access_token: string; token_type: string }>('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });

export const register = (email: string, password: string) =>
  request<User>('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password }),
  });

export const logout = () =>
  request('/api/auth/logout', { method: 'POST' });

export const me = () =>
  request<User>('/api/auth/me');
```

---

## `frontend/src/api/chat.ts`

```typescript
import { request } from './client';
import type { Session, Message } from '../types';

export const createSession = (llm_provider: string, llm_model?: string) =>
  request<Session>('/api/chat/sessions', {
    method: 'POST',
    body: JSON.stringify({ llm_provider, llm_model: llm_model || null }),
  });

export const listSessions = () =>
  request<Session[]>('/api/chat/sessions');

export const getSession = (id: number) =>
  request<{ session: Session; messages: Message[] }>(`/api/chat/sessions/${id}`);

export const deleteSession = (id: number) =>
  request(`/api/chat/sessions/${id}`, { method: 'DELETE' });
```

---

## `frontend/src/hooks/useAuth.ts`

```typescript
import { useState, useCallback } from 'react';
import * as authApi from '../api/auth';
import type { User } from '../types';

function getStoredUser(): User | null {
  try {
    const raw = localStorage.getItem('current_user');
    return raw ? (JSON.parse(raw) as User) : null;
  } catch {
    return null;
  }
}

export function useAuth() {
  const [user, setUser] = useState<User | null>(getStoredUser);
  const token = localStorage.getItem('auth_token');

  const login = useCallback(async (email: string, password: string) => {
    const { data, error } = await authApi.login(email, password);
    if (error || !data) return error ?? 'Login failed';
    localStorage.setItem('auth_token', data.access_token);
    const { data: me } = await authApi.me();
    if (me) {
      localStorage.setItem('current_user', JSON.stringify(me));
      setUser(me);
    }
    return null;
  }, []);

  const register = useCallback(async (email: string, password: string) => {
    const { error } = await authApi.register(email, password);
    if (error) return error;
    return login(email, password);
  }, [login]);

  const logout = useCallback(async () => {
    await authApi.logout();
    localStorage.removeItem('auth_token');
    localStorage.removeItem('current_user');
    setUser(null);
  }, []);

  return { user, token, login, register, logout };
}
```

---

## `frontend/src/hooks/useChat.ts`

```typescript
import { useState, useEffect, useRef, useCallback } from 'react';
import type { Message, Session } from '../types';

const WS_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000')
  .replace(/^https/, 'wss')
  .replace(/^http/, 'ws');

export function useChat(sessionId: number | null, session: Session | null, initialMessages: Message[] = []) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [wsStatus, setWsStatus] = useState<'connecting' | 'connected' | 'disconnected' | 'error'>('disconnected');
  const wsRef = useRef<WebSocket | null>(null);
  const pendingRef = useRef('');
  const initialMessagesRef = useRef(initialMessages);
  initialMessagesRef.current = initialMessages;

  useEffect(() => {
    setMessages(initialMessagesRef.current);
    setIsStreaming(false);
    pendingRef.current = '';

    if (!sessionId) return;
    const token = localStorage.getItem('auth_token');
    if (!token) return;

    setWsStatus('connecting');
    const ws = new WebSocket(
      `${WS_BASE}/api/chat/ws/${sessionId}?token=${encodeURIComponent(token)}`
    );
    wsRef.current = ws;

    ws.onopen = () => setWsStatus('connected');

    ws.onclose = (e) => {
      setWsStatus(e.code === 4001 || e.code === 4004 ? 'error' : 'disconnected');
      setIsStreaming(false);
    };

    ws.onerror = () => setWsStatus('error');

    ws.onmessage = (evt) => {
      let msg: { type: string; content?: string; detail?: string };
      try { msg = JSON.parse(evt.data); } catch { return; }

      if (msg.type === 'token') {
        pendingRef.current += msg.content ?? '';
        const snapshot = pendingRef.current;
        setMessages(prev => {
          const last = prev[prev.length - 1];
          if (last?.streaming) {
            return [...prev.slice(0, -1), { ...last, content: snapshot }];
          }
          return [...prev, { id: Date.now(), role: 'assistant', content: snapshot, streaming: true }];
        });

      } else if (msg.type === 'done') {
        setMessages(prev => prev.map((m, i) =>
          i === prev.length - 1 ? { ...m, streaming: false } : m
        ));
        pendingRef.current = '';
        setIsStreaming(false);

      } else if (msg.type === 'error') {
        pendingRef.current = '';
        setIsStreaming(false);
      }
    };

    return () => {
      ws.close();
      wsRef.current = null;
      setWsStatus('disconnected');
    };
  }, [sessionId]);

  const send = useCallback((text: string) => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN || isStreaming || !text.trim()) return;
    setMessages(prev => [...prev, { id: Date.now(), role: 'user', content: text }]);
    setIsStreaming(true);
    ws.send(JSON.stringify({
      message: text,
      llm_provider: session?.llm_provider,
      llm_model: session?.llm_model ?? undefined,
    }));
  }, [isStreaming, session]);

  return { messages, isStreaming, wsStatus, send };
}
```

---

## `frontend/src/components/ProtectedRoute.tsx`

```tsx
import { Navigate } from 'react-router-dom';

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = localStorage.getItem('auth_token');
  return token ? <>{children}</> : <Navigate to="/login" replace />;
}
```

---

## `frontend/src/components/ProviderBadge.tsx`

```tsx
const PROVIDER_MAP: Record<string, { label: string; cls: string }> = {
  claude: { label: 'Claude', cls: 'badge--claude' },
  openai: { label: 'GPT',    cls: 'badge--openai' },
  gemini: { label: 'Gemini', cls: 'badge--gemini' },
};

export function ProviderBadge({ provider }: { provider: string }) {
  const { label, cls } = PROVIDER_MAP[provider] ?? { label: provider, cls: 'badge--default' };
  return <span className={`provider-badge ${cls}`}>{label}</span>;
}
```

---

## `frontend/src/components/SessionList.tsx`

```tsx
import type { Session } from '../types';
import { ProviderBadge } from './ProviderBadge';

interface Props {
  sessions: Session[];
  activeId: number | null;
  onSelect: (id: number) => void;
  onNew: () => void;
}

export function SessionList({ sessions, activeId, onSelect, onNew }: Props) {
  return (
    <div className="sessions-panel">
      <div className="sessions-header">
        <span className="sessions-title">Conversations</span>
        <button className="btn btn-primary btn-sm" onClick={onNew}>+ New</button>
      </div>
      <div className="sessions-list">
        {sessions.length === 0 && (
          <div className="sessions-empty">No conversations yet</div>
        )}
        {sessions.map(s => (
          <div
            key={s.id}
            className={`session-item ${s.id === activeId ? 'active' : ''}`}
            onClick={() => onSelect(s.id)}
          >
            <div className="session-title">{s.title || 'New Conversation'}</div>
            <div className="session-meta">
              <ProviderBadge provider={s.llm_provider} />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## `frontend/src/components/MessageList.tsx`

```tsx
import { useEffect, useRef } from 'react';
import type { Message } from '../types';

function esc(s: string): string {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

export function MessageList({ messages }: { messages: Message[] }) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="messages">
      {messages.map(m => (
        <div key={m.id} className={`bubble bubble-${m.role}`}>
          <div className="bubble-avatar">{m.role === 'user' ? 'You' : 'AI'}</div>
          <div className="bubble-body">
            {/* textContent-safe: esc() prevents XSS; streaming tokens appended via state update */}
            <div
              className="bubble-text"
              dangerouslySetInnerHTML={{ __html: esc(m.content) + (m.streaming ? '<span class="cursor">▌</span>' : '') }}
            />
          </div>
        </div>
      ))}
      <div ref={endRef} />
    </div>
  );
}
```

---

## `frontend/src/components/ChatInput.tsx`

```tsx
import { useState, useRef, useCallback } from 'react';

interface Props {
  onSend: (text: string) => void;
  disabled: boolean;
}

export function ChatInput({ onSend, disabled }: Props) {
  const [text, setText] = useState('');
  const taRef = useRef<HTMLTextAreaElement>(null);

  const submit = useCallback(() => {
    const trimmed = text.trim();
    if (!trimmed || disabled) return;
    onSend(trimmed);
    setText('');
    if (taRef.current) {
      taRef.current.style.height = 'auto';
    }
  }, [text, disabled, onSend]);

  return (
    <div className="input-area">
      <div className="input-wrapper">
        <textarea
          ref={taRef}
          className="chat-textarea"
          value={text}
          placeholder="Type a message… (Enter to send, Shift+Enter for newline)"
          rows={1}
          disabled={disabled}
          onChange={e => {
            setText(e.target.value);
            e.target.style.height = 'auto';
            e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px';
          }}
          onKeyDown={e => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              submit();
            }
          }}
        />
        <button
          className="send-btn"
          onClick={submit}
          disabled={disabled || !text.trim()}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
            <path d="M22 2L11 13M22 2L15 22L11 13M22 2L2 9L11 13"
              stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
        </button>
      </div>
    </div>
  );
}
```

---

## `frontend/src/pages/Login.tsx`

```tsx
import { useState, FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export function Login() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');
    const err = await login(email, password);
    setLoading(false);
    if (err) { setError(err); return; }
    navigate('/chat');
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1 className="auth-title">Sign in</h1>
        <form onSubmit={handleSubmit} className="auth-form">
          <label>Email</label>
          <input type="email" value={email} onChange={e => setEmail(e.target.value)}
            className="form-input" required autoFocus />
          <label>Password</label>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)}
            className="form-input" required />
          {error && <div className="form-error">{error}</div>}
          <button type="submit" className="btn btn-primary btn-full" disabled={loading}>
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
        <p className="auth-footer">
          No account? <Link to="/register">Register</Link>
        </p>
      </div>
    </div>
  );
}
```

---

## `frontend/src/pages/Register.tsx`

```tsx
import { useState, FormEvent } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

export function Register() {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError('');
    const err = await register(email, password);
    setLoading(false);
    if (err) { setError(err as string); return; }
    navigate('/chat');
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <h1 className="auth-title">Create account</h1>
        <form onSubmit={handleSubmit} className="auth-form">
          <label>Email</label>
          <input type="email" value={email} onChange={e => setEmail(e.target.value)}
            className="form-input" required autoFocus />
          <label>Password</label>
          <input type="password" value={password} onChange={e => setPassword(e.target.value)}
            className="form-input" required minLength={8} />
          {error && <div className="form-error">{error}</div>}
          <button type="submit" className="btn btn-primary btn-full" disabled={loading}>
            {loading ? 'Creating account…' : 'Create account'}
          </button>
        </form>
        <p className="auth-footer">
          Have an account? <Link to="/login">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
```

---

## `frontend/src/pages/Chat.tsx`

```tsx
import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useChat } from '../hooks/useChat';
import { SessionList } from '../components/SessionList';
import { MessageList } from '../components/MessageList';
import { ChatInput } from '../components/ChatInput';
import { ProviderBadge } from '../components/ProviderBadge';
import * as chatApi from '../api/chat';
import type { Session, Message } from '../types';

type Panel = 'empty' | 'new-session' | 'active';

export function Chat() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSession, setActiveSession] = useState<Session | null>(null);
  const [sessionHistory, setSessionHistory] = useState<Message[]>([]);
  const [panel, setPanel] = useState<Panel>('empty');
  const [provider, setProvider] = useState('claude');
  const [model, setModel] = useState('');

  const { messages, isStreaming, wsStatus, send } =
    useChat(activeSession?.id ?? null, activeSession, sessionHistory);

  const loadSessions = useCallback(async () => {
    const { data } = await chatApi.listSessions();
    if (data) setSessions(data);
  }, []);

  useEffect(() => { loadSessions(); }, [loadSessions]);

  async function openSession(id: number) {
    const { data, error } = await chatApi.getSession(id);
    if (error || !data) return;
    setSessionHistory(data.messages);
    setActiveSession(data.session);
    setPanel('active');
    await loadSessions();
  }

  async function createSession() {
    const { data, error } = await chatApi.createSession(provider, model || undefined);
    if (error || !data) { alert(error); return; }
    await loadSessions();
    await openSession(data.id);
  }

  async function deleteSession() {
    if (!activeSession) return;
    if (!confirm('Delete this conversation?')) return;
    await chatApi.deleteSession(activeSession.id);
    setActiveSession(null);
    setPanel('empty');
    await loadSessions();
  }

  async function handleLogout() {
    await logout();
    navigate('/login');
  }

  return (
    <div className="chat-app">
      <aside className="sidebar">
        <div className="sidebar-logo">LLM Chat</div>
        <div className="sidebar-user">
          <span>{user?.email}</span>
          <button className="btn-logout" onClick={handleLogout} title="Logout">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4M16 17l5-5-5-5M21 12H9"
                stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            </svg>
          </button>
        </div>
      </aside>

      <SessionList
        sessions={sessions}
        activeId={activeSession?.id ?? null}
        onSelect={openSession}
        onNew={() => setPanel('new-session')}
      />

      <main className="chat-main">
        {panel === 'empty' && (
          <div className="empty-state">
            <p>Select a conversation or start a new one</p>
            <button className="btn btn-primary" onClick={() => setPanel('new-session')}>
              Start Chatting
            </button>
          </div>
        )}

        {panel === 'new-session' && (
          <div className="new-session-form">
            <h2>New Conversation</h2>
            <label>LLM Provider</label>
            <select value={provider} onChange={e => setProvider(e.target.value)} className="form-input">
              <option value="claude">Claude (Anthropic)</option>
              <option value="openai">GPT (OpenAI)</option>
              <option value="gemini">Gemini (Google)</option>
            </select>
            <label>Model <span className="label-hint">(optional — leave blank for default)</span></label>
            <input
              value={model}
              onChange={e => setModel(e.target.value)}
              className="form-input"
              placeholder="e.g. claude-sonnet-4-6, gpt-4o-mini, gemini-2.0-flash"
            />
            <div className="form-actions">
              <button className="btn btn-primary" onClick={createSession}>Create</button>
              <button className="btn btn-outline" onClick={() => setPanel('empty')}>Cancel</button>
            </div>
          </div>
        )}

        {panel === 'active' && activeSession && (
          <div className="active-chat">
            <div className="chat-header">
              <div className="chat-header-info">
                <span className="chat-title">{activeSession.title || 'Conversation'}</span>
                <ProviderBadge provider={activeSession.llm_provider} />
              </div>
              <button className="btn btn-outline btn-sm btn-danger" onClick={deleteSession}>
                Delete
              </button>
            </div>
            <MessageList messages={messages} />
            <div className="ws-status" data-status={wsStatus} />
            <ChatInput onSend={send} disabled={isStreaming || wsStatus !== 'connected'} />
          </div>
        )}
      </main>
    </div>
  );
}
```

---

## `frontend/src/App.tsx`

```tsx
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Chat } from './pages/Chat';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/chat" element={
          <ProtectedRoute><Chat /></ProtectedRoute>
        } />
        <Route path="/" element={<Navigate to="/chat" replace />} />
        <Route path="*" element={<Navigate to="/chat" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
```

---

## `frontend/src/main.tsx`

```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles/index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

---

## `frontend/src/styles/index.css`

```css
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

:root {
  --bg:            #ffffff;
  --bg-secondary:  #f8fafc;
  --bg-tertiary:   #f1f5f9;
  --text-primary:  #1e293b;
  --text-secondary:#64748b;
  --border:        #e2e8f0;
  --primary:       #2563eb;
  --primary-hover: #1d4ed8;
  --secondary:     #64748b;
  --success:       #10b981;
  --warning:       #f59e0b;
  --error:         #ef4444;
  --radius:        0.5rem;
}

body {
  background: var(--bg);
  color: var(--text-primary);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 0.9375rem;
  line-height: 1.5;
}

/* ── Auth pages ───────────────────────────────────────────────────────────── */
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1.5rem;
}
.auth-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 2rem;
  width: 100%;
  max-width: 380px;
}
.auth-title { font-size: 1.5rem; font-weight: 700; margin-bottom: 1.5rem; }
.auth-form { display: flex; flex-direction: column; gap: 0.5rem; }
.auth-form label { font-size: 0.875rem; font-weight: 500; color: var(--text-primary); }
.auth-footer { margin-top: 1.25rem; font-size: 0.875rem; color: var(--text-secondary); text-align: center; }
.auth-footer a { color: var(--primary); text-decoration: none; }

/* ── Form elements ────────────────────────────────────────────────────────── */
.form-input {
  width: 100%;
  padding: 0.5rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  background: var(--bg);
  color: var(--text-primary);
  font-size: 0.9375rem;
  outline: none;
  transition: border-color 0.15s;
}
.form-input:focus { border-color: var(--primary); }
.form-error { font-size: 0.875rem; color: var(--error); }
.form-actions { display: flex; gap: 0.75rem; margin-top: 0.5rem; }

/* ── Buttons ──────────────────────────────────────────────────────────────── */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.5rem 1rem;
  border-radius: var(--radius);
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  border: 1px solid transparent;
  transition: filter 0.15s, opacity 0.15s;
}
.btn:disabled { opacity: 0.4; cursor: default; }
.btn-primary { background: var(--primary); color: #fff; }
.btn-primary:hover:not(:disabled) { filter: brightness(1.1); }
.btn-outline {
  background: transparent;
  color: var(--text-primary);
  border-color: var(--border);
}
.btn-outline:hover:not(:disabled) { background: var(--bg-tertiary); }
.btn-sm { padding: 0.3rem 0.65rem; font-size: 0.8125rem; }
.btn-danger { color: var(--error); border-color: var(--error); }
.btn-danger:hover:not(:disabled) { background: rgba(239,68,68,0.1); }
.btn-full { width: 100%; }
.btn-logout {
  background: none; border: none; color: var(--text-secondary);
  cursor: pointer; padding: 0.25rem; border-radius: var(--radius);
  display: flex; align-items: center;
}
.btn-logout:hover { color: var(--text-primary); }

/* ── Chat app layout ──────────────────────────────────────────────────────── */
.chat-app {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

/* Sidebar */
.sidebar {
  width: 56px;
  background: var(--bg-secondary);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem 0;
  gap: 1rem;
  flex-shrink: 0;
}
.sidebar-logo {
  font-size: 0.65rem;
  font-weight: 700;
  color: var(--primary);
  text-align: center;
  writing-mode: vertical-rl;
}
.sidebar-user {
  margin-top: auto;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.65rem;
  color: var(--text-secondary);
}

/* Sessions panel */
.sessions-panel {
  width: 260px;
  flex-shrink: 0;
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  background: var(--bg-secondary);
}
.sessions-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border-bottom: 1px solid var(--border);
}
.sessions-title { font-weight: 600; font-size: 0.875rem; }
.sessions-list { flex: 1; overflow-y: auto; padding: 0.5rem; }
.sessions-empty { padding: 1rem 0.75rem; font-size: 0.875rem; color: var(--text-secondary); }

.session-item {
  padding: 0.625rem 0.75rem;
  border-radius: var(--radius);
  cursor: pointer;
  margin-bottom: 0.25rem;
  transition: background 0.15s;
}
.session-item:hover { background: var(--bg-tertiary); }
.session-item.active { background: var(--primary); color: #fff; }
.session-title {
  font-size: 0.875rem;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.session-meta { margin-top: 0.25rem; }

/* Provider badges */
.provider-badge {
  display: inline-flex;
  align-items: center;
  font-size: 0.6875rem;
  font-weight: 600;
  padding: 0.1875rem 0.5rem;
  border-radius: 9999px;
  border: 1px solid transparent;
  line-height: 1;
}
.badge--claude { background: rgba(124,58,237,.12); color: #7c3aed; border-color: rgba(124,58,237,.25); }
.badge--openai { background: rgba(22,163,74,.12);  color: #16a34a; border-color: rgba(22,163,74,.25); }
.badge--gemini { background: rgba(37,99,235,.12);  color: #2563eb; border-color: rgba(37,99,235,.25); }
.badge--default { background: var(--bg-tertiary); color: var(--text-secondary); border-color: var(--border); }
.session-item.active .provider-badge {
  background: rgba(255,255,255,.2);
  color: #fff;
  border-color: transparent;
}

/* ── Chat main area ───────────────────────────────────────────────────────── */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--bg);
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 1rem;
  color: var(--text-secondary);
  padding: 2rem;
  text-align: center;
}

.new-session-form {
  max-width: 480px;
  width: 100%;
  margin: auto;
  padding: 2.5rem 2rem;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.new-session-form h2 { font-size: 1.25rem; margin-bottom: 0.5rem; }
.new-session-form label { font-size: 0.875rem; font-weight: 500; }
.label-hint { font-weight: 400; color: var(--text-secondary); font-size: 0.8rem; }

.active-chat { flex: 1; display: flex; flex-direction: column; overflow: hidden; }

.chat-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.875rem 1.25rem;
  border-bottom: 1px solid var(--border);
  background: var(--bg);
  flex-shrink: 0;
}
.chat-header-info { display: flex; align-items: center; gap: 0.75rem; }
.chat-title { font-weight: 600; font-size: 0.9375rem; }

/* ── Messages ─────────────────────────────────────────────────────────────── */
.messages {
  flex: 1;
  overflow-y: auto;
  padding: 1.25rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.bubble { display: flex; gap: 0.75rem; align-items: flex-start; max-width: 820px; }
.bubble-user { flex-direction: row-reverse; align-self: flex-end; }

.bubble-avatar {
  width: 32px; height: 32px;
  border-radius: 50%;
  background: var(--bg-tertiary);
  color: var(--text-secondary);
  font-size: 0.65rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.bubble-user .bubble-avatar { background: var(--primary); color: #fff; }

.bubble-body {
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 0.75rem;
  padding: 0.625rem 0.875rem;
  max-width: 680px;
}
.bubble-user .bubble-body { background: var(--primary); border-color: var(--primary); color: #fff; }

.bubble-text {
  font-size: 0.9375rem;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}
.cursor { opacity: 0.6; animation: blink 1s step-end infinite; }
@keyframes blink { 50% { opacity: 0; } }

/* ── Input area ───────────────────────────────────────────────────────────── */
.input-area {
  padding: 1rem 1.25rem;
  border-top: 1px solid var(--border);
  background: var(--bg);
  flex-shrink: 0;
}
.input-wrapper {
  display: flex;
  align-items: flex-end;
  gap: 0.5rem;
  background: var(--bg-secondary);
  border: 1px solid var(--border);
  border-radius: 0.75rem;
  padding: 0.5rem 0.75rem;
  transition: border-color 0.15s;
}
.input-wrapper:focus-within { border-color: var(--primary); }
.chat-textarea {
  flex: 1;
  border: none;
  background: transparent;
  resize: none;
  outline: none;
  font-family: inherit;
  font-size: 0.9375rem;
  line-height: 1.5;
  color: var(--text-primary);
  max-height: 200px;
}
.send-btn {
  width: 36px; height: 36px;
  border: none;
  border-radius: var(--radius);
  background: var(--primary);
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: filter 0.15s, opacity 0.15s;
}
.send-btn:hover:not(:disabled) { filter: brightness(1.1); }
.send-btn:disabled { opacity: 0.4; cursor: default; }

/* WS status dot */
.ws-status {
  height: 2px;
  background: transparent;
  transition: background 0.3s;
}
.ws-status[data-status="connecting"] { background: #f59e0b; }
.ws-status[data-status="connected"]  { background: #22c55e; }
.ws-status[data-status="error"]      { background: var(--error); }
```
