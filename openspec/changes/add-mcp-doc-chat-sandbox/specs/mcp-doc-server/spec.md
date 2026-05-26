## ADDED Requirements

### Requirement: Streamable HTTP MCP endpoint
The server SHALL accept MCP protocol traffic over a Streamable HTTP transport on a single configurable port, so that an MCP client and the MCP Inspector can connect simultaneously from separate processes.

#### Scenario: Client connects over HTTP
- **WHEN** an MCP client opens an `initialize` session against the server's HTTP endpoint
- **THEN** the server responds with its server-info and the negotiated protocol version
- **AND** subsequent requests over the same session succeed

#### Scenario: Inspector connects concurrently
- **WHEN** the MCP Inspector is pointed at the same HTTP endpoint while a CLI client session is active
- **THEN** both sessions are accepted and operate independently

### Requirement: In-memory document store seeded from disk
The server SHALL load all files from a `docs/` directory into an in-memory store at startup, keyed by filename, and SHALL NOT persist any change made through tools back to disk.

#### Scenario: Seven seed documents loaded on startup
- **WHEN** the server process starts with four `.md` and three `.txt` files in `docs/`
- **THEN** the store contains exactly seven entries, each preserving the file's original text and inferred MIME type (`text/markdown` for `.md`, `text/plain` for `.txt`)

#### Scenario: Restart reverts edits
- **GIVEN** a client has modified a document via a tool call
- **WHEN** the server process restarts
- **THEN** the document's content matches the original on-disk seed, not the modified content

### Requirement: `list_documents` tool
The server SHALL expose a `list_documents` MCP tool that takes no arguments and returns the id, MIME type, and current length (in characters) of every document in the store.

#### Scenario: List returns all seven documents
- **WHEN** a client calls `tools/call` with name `list_documents` and no arguments
- **THEN** the response contains an entry for each of the seven seeded documents with its id, MIME type, and length

### Requirement: `view_document` tool
The server SHALL expose a `view_document` MCP tool that takes a document `id` and returns the current text content.

#### Scenario: View an existing document
- **WHEN** a client calls `tools/call` with name `view_document` and the id of a seeded document
- **THEN** the response contains the document's current text

#### Scenario: View an unknown document
- **WHEN** a client calls `view_document` with an id that does not exist in the store
- **THEN** the tool call returns an MCP tool error with a short human-readable message

### Requirement: `replace_document` tool
The server SHALL expose a `replace_document` MCP tool that takes a document `id` and a `content` string, replaces the document's content in the in-memory store, and returns the id and the new length.

#### Scenario: Replace updates the store
- **GIVEN** a document with id `notes.md` exists
- **WHEN** a client calls `replace_document` with id `notes.md` and new content
- **THEN** the call succeeds, the returned length matches the new content
- **AND** a subsequent `view_document` for `notes.md` returns the new content

#### Scenario: Replace an unknown document
- **WHEN** a client calls `replace_document` with an id that does not exist
- **THEN** the call returns an MCP tool error and the store is unchanged

### Requirement: `append_document` tool
The server SHALL expose an `append_document` MCP tool that takes a document `id` and a `content` string, appends the content to the existing document text, and returns the id and the new length.

#### Scenario: Append extends the document
- **GIVEN** a document with id `notes.md` and content `"foo"`
- **WHEN** a client calls `append_document` with id `notes.md` and content `"bar"`
- **THEN** a subsequent `view_document` for `notes.md` returns `"foobar"`

#### Scenario: Append to unknown document
- **WHEN** a client calls `append_document` with an unknown id
- **THEN** the call returns an MCP tool error

### Requirement: One MCP resource per document
The server SHALL expose every document in the store as an MCP resource under a `doc://<id>` URI scheme, advertise them via `resources/list`, and serve their current text via `resources/read` with the correct MIME type.

#### Scenario: Listing resources returns all documents
- **WHEN** a client calls `resources/list`
- **THEN** the response contains one resource per document with URI `doc://<id>`, a human-readable name, and the MIME type matching the file extension

#### Scenario: Reading a resource returns current content
- **GIVEN** the content of `doc://notes.md` was updated via `replace_document`
- **WHEN** a client calls `resources/read` with URI `doc://notes.md`
- **THEN** the response contains the updated text, not the original seed

### Requirement: `summarize` prompt
The server SHALL expose a `summarize` MCP prompt that takes a required `doc_id` argument and returns a message instructing the model to summarize the named document, with the document's current content embedded in the prompt.

#### Scenario: Get summarize prompt with a valid document
- **WHEN** a client calls `prompts/get` with name `summarize` and `{doc_id: "notes.md"}`
- **THEN** the response contains one or more user-role messages whose text references the document and embeds its current content

#### Scenario: Summarize prompt for unknown document
- **WHEN** a client calls `prompts/get` for `summarize` with an unknown `doc_id`
- **THEN** the server returns a prompt-level error indicating the document is unknown

### Requirement: `improve` prompt
The server SHALL expose an `improve` MCP prompt that takes a required `doc_id` argument and an optional `tone` argument, and returns a message asking the model to suggest writing improvements to the document.

#### Scenario: Improve prompt with default tone
- **WHEN** a client calls `prompts/get` with name `improve` and `{doc_id: "notes.md"}`
- **THEN** the response embeds the document content and asks for general writing improvements

#### Scenario: Improve prompt with custom tone
- **WHEN** a client calls `prompts/get` with name `improve` and `{doc_id: "notes.md", tone: "formal"}`
- **THEN** the returned message instructs the model to use the specified tone

### Requirement: `grammar` prompt
The server SHALL expose a `grammar` MCP prompt that takes a required `doc_id` argument and returns a message asking the model to correct grammar issues in the document.

#### Scenario: Get grammar prompt
- **WHEN** a client calls `prompts/get` with name `grammar` and `{doc_id: "notes.md"}`
- **THEN** the response embeds the document content and asks for grammar corrections
