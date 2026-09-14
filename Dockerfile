# One image, one process: FastAPI serves both the API and the built frontend
# (api.py's FRONTEND_DIST mount), so a deployment needs nothing beyond this container —
# no separate static host, no CORS configuration, no per-environment base URL.

# --- Stage 1: build the frontend -------------------------------------------------------
FROM node:22-slim AS frontend

# One level above /app: app/src/api/types.test.ts imports config/metafeatures.json via a
# relative path out of the app/ directory, the same file the Python side reads too — one
# vocabulary, not two copies of the study's Literal types drifting apart (D-027).
COPY config/ /config/

WORKDIR /app
COPY app/package.json app/package-lock.json ./
RUN npm ci
COPY app/ ./
RUN npm run build

# --- Stage 2: the Python app, serving that build ----------------------------------------
FROM python:3.12-slim AS backend

# uv installs deps from the lockfile — the same tool and the same lock CI already uses,
# so a deploy resolves the identical versions the test suite ran against.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /usr/local/bin/

WORKDIR /srv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY src/ ./src/
COPY config/ ./config/
COPY data/model/ ./data/model/
COPY README.md ./
RUN uv sync --frozen --no-dev

COPY --from=frontend /app/dist/ ./app/dist/

ENV PATH="/srv/.venv/bin:$PATH"
EXPOSE 8000

# Render (and most single-service hosts) set $PORT; 8000 is the documented local default
# (README, Makefile) when nothing overrides it.
CMD ["sh", "-c", "uvicorn mlsandbox.api:app --host 0.0.0.0 --port ${PORT:-8000}"]
