# syntax=docker/dockerfile:1
FROM python:3.10-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Install dependencies (bỏ --frozen để resolve lại nếu lock outdated)
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --no-install-project --no-dev

# Copy application code
COPY configs/ ./configs/
COPY engine/ ./engine/
COPY main.py ./
COPY app-config.yaml ./

# Final stage
FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=base /app/.venv /app/.venv
COPY --from=base /app/configs ./configs/
COPY --from=base /app/engine ./engine/
COPY --from=base /app/main.py ./
COPY --from=base /app/app-config.yaml ./

RUN useradd --create-home --shell /bin/bash appuser && \
    chown -R appuser:appuser /app
USER appuser

CMD ["python", "main.py"]