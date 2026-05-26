# mcp-doc-chat-sandbox

A learning sandbox for the three core MCP primitives — **tools**, **resources**, and **prompts** — using a real Anthropic LLM. Everything runs in Docker; the host machine needs only `docker` and `docker compose`.

## Architecture

```
┌──────────────────┐       ┌──────────────────────┐
│   cli-chat       │ HTTP  │   mcp-server         │
│   (Python)       │──────▶│   (Python, FastMCP)  │
│                  │       │                      │
│  HOST + CLIENT   │       │  tools:              │
│  ─────────────   │       │    list_documents    │
│  chat loop       │       │    view_document     │
│  Claude API  ────┼──────▶│    replace_document  │
│  / → prompts     │       │    append_document   │
│  @ → resources   │       │                      │
│                  │       │  resources:          │
│  ANTHROPIC_      │       │    doc://<id> ×7     │
│  API_KEY (.env)  │       │                      │
└──────────────────┘       │  prompts:            │
                           │    summarize         │
                           │    improve           │
                           │    grammar           │
                           │                      │
                           │  7 docs in memory    │
                           └──────────────────────┘
                                     ▲
                                     │ HTTP
                           ┌─────────┴────────────┐
                           │  mcp-inspector        │
                           │  web UI → :6274       │
                           └───────────────────────┘
```

## Quickstart

### 1. Set up secrets

```bash
cp .env.example .env
# Edit .env and set ANTHROPIC_API_KEY=sk-ant-...
```

### 2. Start the server and inspector

```bash
docker compose up -d mcp-server mcp-inspector
```

Both services build on first run (takes ~2 min). On subsequent runs they start in seconds.

### 3. Open the Inspector (optional)

Open [http://localhost:6274](http://localhost:6274) in your browser.
Connect it to `http://localhost:8000/mcp` to inspect MCP traffic in real time.

### 4. Start the chat

```bash
docker compose run --rm cli-chat
```

The CLI attaches to your terminal. Type naturally — Claude will use MCP tools to read and modify documents.

## Chat UX

### Plain messages

```
you> list my documents
you> summarize the notes
you> add "remember to update the README" to the end of todo.txt
```

Claude decides which tools to call. You can see the calls in stderr (set `LOG_LEVEL=INFO` in `.env`) and in the Inspector UI.

### `/` — prompt picker

```
you> /                     ← lists available prompts
you> /summarize            ← runs the summarize prompt (asks for doc_id)
you> /improve notes.md     ← runs improve with doc_id=notes.md
you> /grammar todo.txt
```

Prompts are defined on the **server** and returned as ready-to-use message templates.

### `@` — resource picker

```
you> @                         ← lists available resources
you> @notes.md ¿está bien escrito?
```

`@notes.md` inlines the document content directly into your message **before** sending to Claude. The model receives the full text — no extra tool call needed. This demonstrates the *application-controlled* nature of MCP resources (vs tools, which the model controls).

## Documents

Seven seed documents are loaded at startup (4×`.md`, 3×`.txt`):

| File | Type |
|---|---|
| `notes.md` | Meeting notes |
| `ideas.md` | Product backlog |
| `project-overview.md` | Project brief |
| `architecture.md` | Architecture notes |
| `todo.txt` | Personal task list |
| `shopping-list.txt` | Office supplies |
| `travel-plans.txt` | Team offsite plan |

The store is **in-memory** — edits made via tools are not saved to disk and are reset on server restart.

## Configuration

All config is via environment variables (set in `.env`):

| Variable | Required | Default |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | — |
| `ANTHROPIC_MODEL` | No | `claude-haiku-4-5-20251001` |
| `MCP_SERVER_URL` | No | `http://mcp-server:8000/mcp` |
| `LOG_LEVEL` | No | `WARNING` |

To enable verbose MCP + Anthropic logging, add `LOG_LEVEL=INFO` to your `.env`.

## Cost note

Using Haiku 4.5 by default. A typical chat session (10–20 turns with tool calls) costs a few cents. Larger models can be set via `ANTHROPIC_MODEL`.

## Stopping

```bash
docker compose down          # stop server + inspector
# cli-chat auto-removes with --rm after you exit
```
