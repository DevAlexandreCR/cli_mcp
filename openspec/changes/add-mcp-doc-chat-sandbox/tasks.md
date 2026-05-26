## 1. Repo scaffolding

- [x] 1.1 Create top-level layout: `mcp_server/`, `cli_chat/`, `docs/`, `docker-compose.yml`, `.env.example`, `.gitignore`, `README.md`
- [x] 1.2 Add `.env` and Python build artifacts (`__pycache__/`, `*.egg-info/`, `.venv/`) to `.gitignore`
- [x] 1.3 Write `.env.example` listing `ANTHROPIC_API_KEY`, `ANTHROPIC_MODEL` (default `claude-haiku-4-5-20251001`), `MCP_SERVER_URL` (default `http://mcp-server:8000/mcp`)
- [x] 1.4 Author 7 seed documents under `docs/`: 4×`.md`, 3×`.txt`, each short and self-contained

## 2. MCP server — package & deps

- [x] 2.1 Create `mcp_server/pyproject.toml` with deps: `mcp[cli]` (Python SDK), pinned versions; configure `uv` build system
- [x] 2.2 Generate `mcp_server/uv.lock` inside the build container (do not run `uv` on host)
- [x] 2.3 Add `mcp_server/Dockerfile`: multi-stage from an `astral-sh/uv` base image, ending in a slim Python runtime; `COPY docs/ /app/docs/`; expose the MCP port

## 3. MCP server — in-memory store

- [x] 3.1 Implement `mcp_server/store.py`: load all files in `/app/docs/` into a dict keyed by filename, recording content and MIME (`text/markdown` for `.md`, `text/plain` for `.txt`)
- [x] 3.2 Provide store methods: `list()`, `get(id)`, `replace(id, content)`, `append(id, content)`, each raising a domain error on unknown id
- [x] 3.3 Confirm restart restores seed content (no disk writes anywhere in the module)

## 4. MCP server — protocol surface

- [x] 4.1 Implement `mcp_server/app.py` using the MCP Python SDK; register the Streamable HTTP transport on the configured port
- [x] 4.2 Register tools: `list_documents`, `view_document`, `replace_document`, `append_document` — each delegating to the store and translating domain errors into MCP tool errors
- [x] 4.3 Register one resource per document under `doc://<id>` with correct MIME; implement `resources/list` and `resources/read`
- [x] 4.4 Register prompts: `summarize(doc_id)`, `improve(doc_id, tone?)`, `grammar(doc_id)`; each fetches current content from the store and returns ready-to-send user-role messages
- [x] 4.5 Add a `mcp_server/__main__.py` entry point so the container runs `python -m mcp_server`

## 5. CLI chat host — package & deps

- [x] 5.1 Create `cli_chat/pyproject.toml` with deps: `mcp` (Python SDK client), `anthropic`, pinned versions; configure `uv` build system
- [x] 5.2 Generate `cli_chat/uv.lock` inside the build container
- [x] 5.3 Add `cli_chat/Dockerfile`: multi-stage uv-based build; the container's default `CMD` runs `python -m cli_chat`

## 6. CLI chat host — config & startup

- [x] 6.1 Implement `cli_chat/config.py`: load `ANTHROPIC_API_KEY` (required, fail fast if missing), `ANTHROPIC_MODEL` (default `claude-haiku-4-5-20251001`), `MCP_SERVER_URL` (default in-network)
- [x] 6.2 Implement `cli_chat/mcp_client.py`: connect to the server over Streamable HTTP, perform `initialize`, expose helpers for `tools/list`, `tools/call`, `resources/list`, `resources/read`, `prompts/list`, `prompts/get`; exit non-zero on connection failure
- [x] 6.3 Print a startup banner with: server URL, model in use, "store is in-memory — restarts wipe edits"

## 7. CLI chat host — chat loop

- [x] 7.1 Implement `cli_chat/anthropic_host.py`: build the `tools` parameter from the MCP tool list, send messages with the Anthropic SDK, return assistant blocks
- [x] 7.2 Implement tool-use loop: while the latest assistant turn contains `tool_use` blocks, call the matching MCP tool, append a `tool_result` block, and re-send; stop when only text is returned
- [x] 7.3 Render tool errors to the terminal as `[tool error: …]` AND return them as error `tool_result` blocks so Claude can adapt
- [x] 7.4 Configure two named loggers — `mcp_client` and `anthropic_host` — so the source of every frame is identifiable in stdout

## 8. CLI chat host — `/` and `@` UX

- [x] 8.1 Implement input parser in `cli_chat/input.py`: recognize bare `/`, `/<name>` (+ optional args), bare `@`, and `@<id>` tokens inside arbitrary text
- [x] 8.2 Bare `/` → call `prompts/list` and print names + short descriptions
- [x] 8.3 `/<name>` → fetch the prompt's schema, prompt the user for required args (and optional `tone` for `improve`), call `prompts/get`, inject returned messages as the next user turn into the chat loop
- [x] 8.4 Bare `@` → call `resources/list` and print id, MIME, label
- [x] 8.5 `@<id>` → fetch via `resources/read`, replace the token with a clearly delimited block (e.g. fenced under a `--- doc://<id> ---` header) carrying current content, then send the full message to Claude
- [x] 8.6 Unknown `/<name>` or `@<id>` → print an error and skip the Anthropic call

## 9. Docker Compose orchestration

- [x] 9.1 Write `docker-compose.yml` defining three services: `mcp-server` (built from `mcp_server/`, exposes a network port), `mcp-inspector` (Node container running pinned `@modelcontextprotocol/inspector`, publishes a host port for the web UI), `cli-chat` (built from `cli_chat/`, no published ports, `tty: true` + `stdin_open: true`, `env_file: .env`)
- [x] 9.2 Wire `MCP_SERVER_URL` defaulting (in compose) to `http://mcp-server:<port>/mcp`
- [x] 9.3 Configure dependencies so the inspector and CLI services wait for the server to be reachable (`depends_on` with a healthcheck on the server)
- [ ] 9.4 Verify `docker compose up -d mcp-server mcp-inspector` brings both up cleanly with no logs errors  ← manual

## 10. Inspector container

- [x] 10.1 Add `inspector/Dockerfile` (or inline in compose) based on `node:lts-alpine`, running `npx @modelcontextprotocol/inspector@<pinned-version>`; pin the version in a comment near the directive
- [ ] 10.2 Confirm the Inspector UI opens at `http://localhost:<host-port>` and can target the server URL

## 11. End-to-end smoke checks (manual)

- [ ] 11.1 With server + inspector running, `docker compose run --rm cli-chat`: greet user, accept a plain message, observe a Claude reply
- [ ] 11.2 Ask "list my documents" and observe Claude call `list_documents` (visible in CLI logs and in the Inspector traffic view)
- [ ] 11.3 Ask "summarize notes" and observe a chain of `tool_use` calls (`list_documents` → `view_document`) ending in a text summary
- [ ] 11.4 Type `/summarize notes.md` and confirm the prompt is fetched and the conversation proceeds
- [ ] 11.5 Type `@notes.md ¿está bien escrito?` and confirm the document content was inlined into the user turn (visible in Inspector or logs) and Claude reviewed it
- [ ] 11.6 Type `replace the content of notes.md with "hola"` and confirm `replace_document` is called; subsequent `view_document` returns `"hola"`
- [ ] 11.7 Restart `mcp-server` and confirm `view_document notes.md` returns the original seed content (proves in-memory + reset)
- [ ] 11.8 Stop `cli-chat`, then run again with `ANTHROPIC_API_KEY` removed from `.env` — confirm the host exits with a clear missing-variable error

## 12. README

- [x] 12.1 Write a top-level `README.md` covering: prerequisites (`docker`, `docker compose` only), 30-second quickstart (`cp .env.example .env`, fill in key, `docker compose up -d mcp-server mcp-inspector`, `docker compose run --rm cli-chat`), the `/` and `@` UX, the Inspector URL, and a brief note on cost
- [x] 12.2 Include the architecture diagram (compose services + arrows) and the tool/resource/prompt list as a quick reference
