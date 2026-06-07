#!/usr/bin/env python3
"""Extract verbatim source files from reference markdown files.
Run from the project root: python scripts/extract_references.py
Used by the Dockerfile to materialise backend/ and frontend/ at image build time.
"""
import re
import os
from pathlib import Path

REFS = [
    "references/backend-reference.md",
    "references/frontend-reference.md",
]

# Files not present in the reference markdown (generated from descriptions in SKILL.md)
EMPTY_FILES = [
    "backend/app/__init__.py",
    "backend/app/schemas/__init__.py",
    "backend/app/utils/__init__.py",
    "backend/app/services/__init__.py",
    "backend/app/api/__init__.py",
]

HARDCODED_FILES = {
    "backend/app/models/__init__.py": (
        "from app.models.user import User\n"
        "from app.models.chat import ChatSession, ChatMessage\n"
    ),
    "frontend/index.html": """\
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Chatbot</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
""",
}


def extract_from_ref(ref_path: str) -> dict[str, str]:
    text = Path(ref_path).read_text(encoding="utf-8")
    # Match:  ## `path/to/file`  followed by a fenced code block
    pattern = re.compile(
        r'## `([^`]+)`\s*\n+```\w*\n(.*?)```',
        re.DOTALL,
    )
    return {m.group(1): m.group(2) for m in pattern.finditer(text)}


def write(path: str, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content, encoding="utf-8")
    print(f"  wrote  {path}")


total = 0

for ref in REFS:
    for path, content in extract_from_ref(ref).items():
        write(path, content)
        total += 1

for path in EMPTY_FILES:
    write(path, "")
    total += 1

for path, content in HARDCODED_FILES.items():
    write(path, content)
    total += 1

print(f"\n  {total} files written.")
