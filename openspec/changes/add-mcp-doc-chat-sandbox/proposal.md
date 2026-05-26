## Why

We want a hands-on sandbox to learn the three core primitives of the Model Context Protocol — tools, resources, and prompts — by building both sides of the wire (server + client) in a small, throwaway, self-contained project. The objective is *understanding*, not shipping: we need a minimal, working setup that exercises each primitive end-to-end with a real LLM in the loop, while keeping the host machine clean (everything runs in Docker).

## What Changes

- Add a Python MCP **server** that holds 7 documents (4×`.md` + 3×`.txt`) entirely in memory and exposes:
  - **Tools**: `list_documents`, `view_document`, `replace_document`, `append_document`
  - **Resources**: one `doc://<id>` per document, with correct MIME types
  - **Prompts**: `summarize`, `improve`, `grammar` (parametrized by document id)
- Add a Python **CLI chat host** that:
  - Drives an Anthropic Claude chat loop (model id from `ANTHROPIC_MODEL` env, defaulting to `claude-haiku-4-5-20251001`)
  - Acts as an MCP client connected to the server over Streamable HTTP
  - Forwards MCP tool definitions to Claude and executes returned `tool_use` calls
  - Interprets `/` as a **prompt picker** (lists `prompts/list`, fetches `prompts/get`, injects the templated messages into the chat)
  - Interprets `@` as a **resource picker** that **inlines** the resource content into the user's next message before sending to Claude (chosen over the "let the LLM decide to fetch it" alternative — see design.md)
- Add a **docker compose** stack with three services: `mcp-server`, `mcp-inspector`, `cli-chat` — none of which require any package installed on the host. `ANTHROPIC_API_KEY` is read from a project-level `.env` file.
- Add a `docs/` folder with 7 seed documents, copied into the server image at build time and loaded into memory on startup. The store is reset on every restart (no persistence).

## Capabilities

### New Capabilities
- `mcp-doc-server`: An in-memory document store exposed through the MCP protocol via tools, resources, and prompts.
- `mcp-cli-host`: An interactive CLI that hosts an LLM chat session and acts as an MCP client, with `/` and `@` affordances for prompts and resources.
- `containerized-runtime`: A docker-compose orchestration that runs server, host, and MCP Inspector with zero host-side installs and `.env`-based secrets.

### Modified Capabilities
<!-- None — no prior specs exist. -->

## Impact

- **New code**: Python package(s) for the server and the host, a `Dockerfile` per service, a top-level `docker-compose.yml`, an `.env.example`, and the seed `docs/` folder.
- **New dependencies**: `mcp` (Python SDK), `anthropic` (LLM SDK), plus whatever each pulls in. JS deps for the inspector live inside its container only.
- **External services**: Anthropic API (paid usage). Costs are bounded by the small doc corpus and short chat sessions; Haiku is the default for cost reasons.
- **Host machine**: Untouched — only `docker` and `docker compose` are required. No Python, no Node, no `uv` installed on the host.
- **Out of scope**: persistence, auth, multi-user, streaming UI, real file I/O on disk, PDF support, find/replace edit semantics, prompt caching, batch APIs, conversation persistence between restarts.
