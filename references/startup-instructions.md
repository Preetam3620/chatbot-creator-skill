# Startup Instructions

Print the block below exactly as written after all files have been created.

```
============================================================
  Chatbot App — Setup Complete
============================================================

BACKEND
  cd backend
  python -m venv venv
  # Windows:  venv\Scripts\activate
  # macOS/Linux:  source venv/bin/activate
  pip install -r requirements.txt

  cp .env.example .env
  # Edit .env:
  #   SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(32))">
  #   ANTHROPIC_API_KEY=sk-ant-...   (or OPENAI_API_KEY / GEMINI_API_KEY)

  uvicorn app.main:app --reload --port 8000
  # Tables auto-created on first start. API docs: http://localhost:8000/docs

FRONTEND
  cd ../frontend
  npm install
  cp .env.example .env          # VITE_API_URL=http://localhost:8000
  npm run dev
  # App: http://localhost:5173

QUICK TEST
  1. Open http://localhost:5173 → redirects to /login
  2. Register a new account → auto-logged in
  3. Click "+ New" → select Claude → Create
  4. Send a message → watch tokens stream in
  5. Refresh → history loads from SQLite
  6. npm run build  (in frontend/) → must pass TypeScript checks

============================================================
```
