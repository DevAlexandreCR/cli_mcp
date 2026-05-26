## Context

This is the first piece of code in the repo — there is no existing system to integrate with, no legacy to preserve, no other services to coordinate with. The driver is *learning*: we want to feel each of MCP's three primitives (tools, resources, prompts) from both sides of the wire while keeping the host machine untouched. The chat loop is mediated by a real LLM (Anthropic Claude) so that tool selection happens organically, not via hard-coded user commands.

Constraints baked into the brief:
- Python, `uv`, the official `mcp` Python SDK, the `anthropic` SDK, and MCP Inspector.
- Nothing installed on the host beyond `docker` / `docker compose`.
- `ANTHROPIC_API_KEY` lives in `.env` and is never committed.
- The doc store is in-memory only; restarts wipe edits.

## Goals / Non-Goals

**Goals:**
- Three-service docker-compose stack: `mcp-server`, `mcp-inspector`, `cli-chat`.
- A single sandbox where the developer can issue natural-language requests ("resume el doc de notas"), watch Claude pick MCP tools, and inspect every frame in the Inspector UI.
- Concrete demonstrations of all three primitives:
  - **Tools** invoked by Claude (`list_documents`, `view_document`, `replace_document`, `append_document`).
  - **Resources** inlined by the host when the user types `@<doc>`.
  - **Prompts** fetched and injected when the user types `/<prompt>`.
- One Anthropic round-trip per conversation turn (looped while Claude returns `tool_use`), no streaming.

**Non-Goals:**
- Persistence, accounts, multi-user, real file editing on host disk.
- PDF support (replaced by `.txt` to keep handling uniform).
- Production polish: retries, exponential backoff, telemetry, prompt caching, rate-limit handling.
- Conversation persistence across restarts.
- Find/replace edit semantics; only whole-document replace and append.
- A slick TUI — `input()` + a line printer is enough.

## Decisions

### Transport: Streamable HTTP (not stdio)
The server speaks MCP over HTTP so two independent containers (the CLI host and the Inspector) can connect to it simultaneously over the docker network. Stdio would force the client to spawn the server as a subprocess — impossible across container boundaries without complex IPC, and incompatible with using the Inspector as a separate service. Streamable HTTP is the modern MCP transport, well supported by the Python SDK and the Inspector, and is the natural pattern for `docker compose`.

### Host = LLM client AND MCP client (single process)
The CLI container plays both roles. It owns the chat loop, talks to the Anthropic API with the MCP tool list flattened into Anthropic's `tools` parameter, and routes `tool_use` blocks back to the MCP server via the MCP client SDK. Splitting these into two containers would buy nothing here — they share state (conversation history, MCP session).

### `@resource` injects the content directly (Option A)
When the user types `@notes.md ¿esto está bien escrito?`, the host calls `resources/read` on the server, gets the content, and **inlines** it into the user message before sending to Claude — e.g. as a fenced block with the resource URI as a header. Considered alternative: just mention the URI and let Claude call `view_document` itself. We chose A because (a) it matches the Claude Desktop / Claude Code UX the user already knows, (b) it saves a round-trip, and (c) it makes the *application-controlled* nature of resources visible — the user, not the model, decides what enters the context. This is the lesson we want to internalize.

### `/prompt` fetches a server-rendered prompt and injects it as the user turn
The server's prompts return ready-to-send messages (already populated with the chosen document's content). The host shows the user a picker, prompts for required arguments, calls `prompts/get`, and submits the resulting message(s) as the next user turn. This keeps prompt logic on the server (where it can evolve) and the client thin.

### Tool surface: 4 tools, intentionally minimal
- `list_documents() → [{id, mime, length}]`
- `view_document(id) → text`
- `replace_document(id, content) → {id, length}`
- `append_document(id, content) → {id, length}`
No `find_replace`, no `delete`, no `create`. Edits operate on `.md` *and* `.txt` uniformly (no read-only resources now that PDFs are dropped). Errors are returned as MCP tool errors with a short message.

### Seed corpus = 7 files on disk, loaded into memory on startup
A `docs/` folder is copied into the server image at build time and contains 7 files (4×`.md` + 3×`.txt`). On startup the server reads each file into a `dict[str, Document]` keyed by filename. This is what "in memory" means in this project: there is no DB, edits never touch disk, and a restart re-seeds from the baked-in originals. Authoring docs as files is much nicer than hardcoding them in Python and still satisfies the "memory-only" constraint at runtime.

### Default model: Claude Haiku 4.5 (`claude-haiku-4-5-20251001`)
Override with `ANTHROPIC_MODEL` env. Haiku is the cheapest and fastest current model — appropriate for a learning sandbox where we'll be hitting the API a lot while iterating. Tool-use quality is fine for this scope.

### Compose UX: `up -d` for daemons, `run --rm` for the CLI
`mcp-server` and `mcp-inspector` run detached. `cli-chat` is invoked interactively via `docker compose run --rm cli-chat` so it attaches to the developer's TTY (the user can type, see Claude's replies, type `/` and `@`). Trying to run an interactive CLI via `docker compose up` is awkward in practice.

### `.env` handling
A top-level `.env` (gitignored) holds `ANTHROPIC_API_KEY` and optionally `ANTHROPIC_MODEL` and `MCP_SERVER_URL`. Compose's `env_file:` directive feeds it to the `cli-chat` service only — the server and inspector don't need it. An `.env.example` is checked in.

### Dependency management: `uv`, locked per service
Each Python service (`mcp-server`, `cli-chat`) has its own `pyproject.toml` and `uv.lock`. `uv` is used inside the Dockerfile (multi-stage: a `uv` base image, then a slim runtime). This honors the "use uv" requirement without installing it on the host.

### Inspector: official image if available, otherwise a thin Node container
Run `@modelcontextprotocol/inspector` via `npx` inside a small `node:lts-alpine` container. The Inspector's web UI is published on a host port (e.g. `5173`) so the developer opens it in a normal browser. It connects to the server using the in-network URL (e.g. `http://mcp-server:8000/mcp`).

## Risks / Trade-offs

- **[LLM cost during iteration]** → Default to Haiku 4.5; make it trivial to switch via env; document expected cost order-of-magnitude in the README ("cents per session").
- **[`ANTHROPIC_API_KEY` leak via git]** → `.env` is in `.gitignore` from day one; only `.env.example` is committed; README explicitly tells the dev to copy and fill in.
- **[Inspector image drift / no official image]** → Pin the inspector npm package version in the Dockerfile so an upstream change can't silently break the stack. If an official image lands later, swap to it.
- **[Restart wipes user edits]** → This is intended (it's a sandbox), but is the kind of thing that surprises someone returning to the project days later. The CLI prints a one-line banner on startup explaining the in-memory store, so the behavior is discoverable.
- **[Inlined `@resource` blows up the context window for big docs]** → All 7 seed docs are intentionally short. The host could later cap inlined content with a length warning; not in scope for v1.
- **[Tool errors are silent in the chat UX]** → Surfaced as a visible "[tool error: …]" line in the CLI so the developer can see what went wrong without digging into logs.
- **[Two SDKs in one process can mask which is failing]** → Logging is split with two distinct loggers (`mcp_client`, `anthropic_host`) so the source of every frame is obvious in stdout.

## Open Questions

- Should the server provide a `subscribe` capability for resources so the Inspector can show live edits? Probably not for v1 — adds protocol surface that doesn't teach a new primitive.
- Do we want a `--no-llm` flag on the CLI for offline demos? Tempting but doubles the host code paths. Hold off unless we hit the rate limit during a workshop.
