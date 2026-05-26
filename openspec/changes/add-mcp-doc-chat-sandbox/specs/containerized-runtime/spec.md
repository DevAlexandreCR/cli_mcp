## ADDED Requirements

### Requirement: Three-service docker-compose stack
The project SHALL define a single top-level `docker-compose.yml` with three services: `mcp-server`, `mcp-inspector`, and `cli-chat`. The server and inspector SHALL run as long-lived background services; the CLI SHALL be invoked interactively per session.

#### Scenario: Background services come up cleanly
- **WHEN** the developer runs `docker compose up -d mcp-server mcp-inspector`
- **THEN** both services reach a healthy state with no errors in their logs
- **AND** the MCP server is reachable from within the compose network at `http://mcp-server:<port>/`

#### Scenario: CLI runs interactively
- **WHEN** the developer runs `docker compose run --rm cli-chat`
- **THEN** the container attaches to the developer's TTY and reads stdin
- **AND** exits when the chat loop ends, removing the container

### Requirement: No host-side language toolchains required
Beyond `docker` and `docker compose`, the project SHALL NOT require any language runtime, package manager, or SDK to be installed on the host machine. All Python, `uv`, and Node.js dependencies SHALL live inside their respective container images.

#### Scenario: Clean-host bring-up
- **GIVEN** a host machine with only `docker` and `docker compose` installed
- **WHEN** the developer follows the README from scratch
- **THEN** they can build all images, start the services, and run the CLI without installing Python, `uv`, Node.js, or any package on the host

### Requirement: Secrets supplied via `.env`
The `cli-chat` service SHALL receive `ANTHROPIC_API_KEY` (required), `ANTHROPIC_MODEL` (optional), and `MCP_SERVER_URL` (optional) via a top-level `.env` file consumed by docker-compose's `env_file:` mechanism. The `.env` file SHALL be in `.gitignore`, and an `.env.example` SHALL be committed.

#### Scenario: `.env` populates the CLI environment
- **GIVEN** the developer has copied `.env.example` to `.env` and set a valid `ANTHROPIC_API_KEY`
- **WHEN** the CLI container starts via `docker compose run --rm cli-chat`
- **THEN** the API key is available to the CLI process as an environment variable
- **AND** is not visible to the `mcp-server` or `mcp-inspector` containers

#### Scenario: `.env` is never committed
- **WHEN** the developer inspects the repository's `.gitignore`
- **THEN** `.env` is listed as ignored
- **AND** only `.env.example` is tracked in the repository

### Requirement: MCP Inspector runs in its own container with a pinned version
The `mcp-inspector` service SHALL run `@modelcontextprotocol/inspector` inside a Node.js container at a version pinned in the Dockerfile (or compose file), and SHALL expose its web UI on a published host port.

#### Scenario: Inspector UI is reachable from the host browser
- **WHEN** `docker compose up -d mcp-inspector` is running
- **THEN** the developer can open the inspector UI in a browser at the published host port
- **AND** can target the in-network MCP server URL from that UI

#### Scenario: Inspector version is pinned
- **WHEN** the developer rebuilds the inspector image months later
- **THEN** the build resolves the same major.minor version of `@modelcontextprotocol/inspector` as the original build
