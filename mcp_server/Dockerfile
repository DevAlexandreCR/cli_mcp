# Build stage — generates uv.lock and installs deps
FROM ghcr.io/astral-sh/uv:0.5-python3.12-bookworm-slim AS builder

WORKDIR /app

# Install deps first for layer caching
COPY mcp_server/pyproject.toml pyproject.toml
RUN uv sync --no-dev --no-install-project

# Copy source and install the package itself
COPY mcp_server/mcp_server/ mcp_server/
RUN uv sync --no-dev

# Runtime stage
FROM python:3.12-slim AS runtime

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/mcp_server /app/mcp_server

# Seed documents are baked in at build time; no disk writes at runtime
COPY docs/ /app/docs/

ENV PATH="/app/.venv/bin:$PATH"
ENV DOCS_DIR=/app/docs
ENV PORT=8000

EXPOSE 8000

CMD ["python", "-m", "mcp_server"]
