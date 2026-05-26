## ADDED Requirements

### Requirement: Connect to MCP server on startup
The CLI host SHALL connect to the configured MCP server URL on startup and SHALL fail fast with a clear message if the connection cannot be established.

#### Scenario: Successful connection
- **GIVEN** the MCP server is reachable at the URL given by `MCP_SERVER_URL`
- **WHEN** the CLI host starts
- **THEN** it completes an MCP `initialize` handshake before the first user prompt
- **AND** prints a one-line banner naming the server, the model in use, and the in-memory-store caveat

#### Scenario: Server unreachable
- **GIVEN** the MCP server is not reachable at the configured URL
- **WHEN** the CLI host starts
- **THEN** it prints a human-readable error and exits with a non-zero status before reading user input

### Requirement: Interactive chat loop with Claude
The CLI host SHALL drive a synchronous, turn-based chat loop with the Anthropic API using the model id from `ANTHROPIC_MODEL` (defaulting to `claude-haiku-4-5-20251001`) and the API key from `ANTHROPIC_API_KEY`.

#### Scenario: Plain user message produces a model reply
- **WHEN** the user types a message that contains neither `/` nor `@`
- **THEN** the host sends the message to Claude with the current MCP tool list attached
- **AND** prints Claude's final text response to the terminal

#### Scenario: Missing API key
- **WHEN** `ANTHROPIC_API_KEY` is unset at startup
- **THEN** the host exits with a non-zero status and an error message naming the missing variable, without attempting any API call

### Requirement: Forward MCP tools to Claude and execute tool_use
The CLI host SHALL fetch the MCP server's tool list, translate it into Anthropic's `tools` schema, and execute every `tool_use` block Claude returns by calling the corresponding MCP tool, looping until Claude returns a final text response with no further tool calls.

#### Scenario: Single tool call round-trip
- **WHEN** Claude responds with one `tool_use` block in a turn
- **THEN** the host calls the corresponding MCP tool, sends the result back as a `tool_result` content block, and continues the conversation
- **AND** the resulting final text is what the user sees

#### Scenario: Multiple sequential tool calls
- **WHEN** Claude requests another tool after receiving the previous tool's result
- **THEN** the host executes each requested tool in order and only prints text to the user when Claude stops requesting tools

#### Scenario: Tool error is surfaced to Claude and the user
- **WHEN** an MCP tool call returns an error
- **THEN** the host returns an error `tool_result` to Claude so the model can adapt
- **AND** prints a visible `[tool error: …]` line to the terminal

### Requirement: `/` opens a prompt picker
When the user input starts with `/`, the CLI host SHALL interpret it as a request to use an MCP prompt provided by the server, by listing available prompts, collecting required arguments, fetching the rendered prompt, and submitting the resulting message as the next user turn.

#### Scenario: Bare `/` lists prompts
- **WHEN** the user submits the single character `/`
- **THEN** the host prints the names and short descriptions of every prompt returned by `prompts/list`

#### Scenario: `/<name>` invokes a prompt
- **WHEN** the user submits `/summarize`
- **THEN** the host prompts for any required arguments, calls `prompts/get`, and uses the returned messages as the user turn into Claude
- **AND** the resulting Claude response is printed to the terminal

#### Scenario: Unknown prompt name
- **WHEN** the user submits `/does-not-exist`
- **THEN** the host prints an error and does not call Claude

### Requirement: `@` injects a resource into the next message
When the user input contains an `@<resource-id>` token, the CLI host SHALL replace the token with the current text content of that resource (fetched via `resources/read`) before sending the message to Claude, so that the user — not the model — controls when a resource enters the context.

#### Scenario: Bare `@` lists resources
- **WHEN** the user submits the single character `@`
- **THEN** the host prints the id, MIME type, and a short label for every resource returned by `resources/list`

#### Scenario: `@<id>` inline expansion
- **WHEN** the user submits `@notes.md please review the wording`
- **THEN** the host fetches `doc://notes.md`, replaces the `@notes.md` token with a clearly delimited block containing the document's current text, and sends the resulting message to Claude
- **AND** the user sees the model's response in the terminal

#### Scenario: Unknown resource id
- **WHEN** the user submits `@does-not-exist some text`
- **THEN** the host prints an error and does not call Claude

### Requirement: Configuration via environment variables
The CLI host SHALL read its configuration exclusively from environment variables: `ANTHROPIC_API_KEY` (required), `ANTHROPIC_MODEL` (optional, defaults to `claude-haiku-4-5-20251001`), and `MCP_SERVER_URL` (optional, defaults to the server's in-network URL).

#### Scenario: Default model is Haiku 4.5
- **GIVEN** `ANTHROPIC_MODEL` is unset
- **WHEN** the host issues an Anthropic API call
- **THEN** the request uses `claude-haiku-4-5-20251001`

#### Scenario: Model override is honored
- **GIVEN** `ANTHROPIC_MODEL=claude-sonnet-4-6` is set
- **WHEN** the host issues an Anthropic API call
- **THEN** the request uses `claude-sonnet-4-6`
