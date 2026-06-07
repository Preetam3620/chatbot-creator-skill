FROM python:3.11-slim

# Install Node 20 via NodeSource
RUN apt-get update && apt-get install -y curl ca-certificates gnupg && \
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && \
    apt-get install -y nodejs && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only the skill's reference files and scripts
COPY references/ ./references/
COPY scripts/ ./scripts/

# Extract all source files from the reference markdown at build time
RUN python scripts/extract_references.py

# Install Python deps
RUN pip install --no-cache-dir -r backend/requirements.txt

# VITE_API_URL="" tells Vite to bake in an empty base URL so all API calls
# use relative paths (same origin). The ?? fallback in client.ts only fires
# when the var is undefined (local dev), not when it is set to empty string.
RUN cd frontend && npm install && VITE_API_URL= npm run build

# Inject built frontend into the backend static dir
RUN mkdir -p backend/app/static && cp -r frontend/dist/. backend/app/static/

WORKDIR /app/backend

EXPOSE 7860

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7860"]
