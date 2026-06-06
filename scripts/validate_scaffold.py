#!/usr/bin/env python3
"""Run from the project root: python scripts/validate_scaffold.py"""
import os, sys

EXPECTED_FILES = [
    # Backend
    "backend/requirements.txt",
    "backend/.env.example",
    "backend/app/__init__.py",
    "backend/app/config.py",
    "backend/app/database.py",
    "backend/app/models/__init__.py",
    "backend/app/models/user.py",
    "backend/app/models/chat.py",
    "backend/app/schemas/__init__.py",
    "backend/app/schemas/auth.py",
    "backend/app/schemas/chat.py",
    "backend/app/utils/__init__.py",
    "backend/app/utils/security.py",
    "backend/app/services/__init__.py",
    "backend/app/services/chat_graph.py",
    "backend/app/api/__init__.py",
    "backend/app/api/auth.py",
    "backend/app/api/chat.py",
    "backend/app/main.py",
    # Frontend
    "frontend/package.json",
    "frontend/vite.config.ts",
    "frontend/tsconfig.json",
    "frontend/tsconfig.node.json",
    "frontend/.env.example",
    "frontend/index.html",
    "frontend/src/types/index.ts",
    "frontend/src/api/client.ts",
    "frontend/src/api/auth.ts",
    "frontend/src/api/chat.ts",
    "frontend/src/hooks/useAuth.ts",
    "frontend/src/hooks/useChat.ts",
    "frontend/src/components/ProtectedRoute.tsx",
    "frontend/src/components/ProviderBadge.tsx",
    "frontend/src/components/SessionList.tsx",
    "frontend/src/components/MessageList.tsx",
    "frontend/src/components/ChatInput.tsx",
    "frontend/src/pages/Login.tsx",
    "frontend/src/pages/Register.tsx",
    "frontend/src/pages/Chat.tsx",
    "frontend/src/App.tsx",
    "frontend/src/main.tsx",
    "frontend/src/styles/index.css",
]

passed, failed = 0, 0
for path in EXPECTED_FILES:
    if os.path.isfile(path):
        print(f"  ✓  {path}")
        passed += 1
    else:
        print(f"  ✗  {path}  ← MISSING")
        failed += 1

print(f"\n  {passed}/{passed + failed} files present")
if failed:
    print(f"  {failed} missing — re-run the relevant build step.")
    sys.exit(1)
else:
    print("  Scaffold complete.")
