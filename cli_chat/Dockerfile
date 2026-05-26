# Build stage
FROM ghcr.io/astral-sh/uv:0.5-python3.12-bookworm-slim AS builder

WORKDIR /app

COPY cli_chat/pyproject.toml pyproject.toml
RUN uv sync --no-dev --no-install-project

COPY cli_chat/cli_chat/ cli_chat/
RUN uv sync --no-dev

# Runtime stage
FROM python:3.12-slim AS runtime

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/cli_chat /app/cli_chat

ENV PATH="/app/.venv/bin:$PATH"
# MCP_SERVER_URL and ANTHROPIC_* come from .env via docker compose

CMD ["python", "-m", "cli_chat"]
