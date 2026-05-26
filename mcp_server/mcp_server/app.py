import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP
import mcp.types as types

from .store import DocumentStore, DocumentNotFoundError

DOCS_DIR = Path(os.environ.get("DOCS_DIR", "/app/docs"))

store = DocumentStore(DOCS_DIR)
mcp = FastMCP("mcp-doc-server")


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@mcp.tool()
def list_documents() -> list[dict]:
    """List all documents with their id, MIME type, and character length."""
    return [{"id": d.id, "mime": d.mime_type, "length": len(d.content)} for d in store.list()]


@mcp.tool()
def view_document(id: str) -> str:
    """Return the current text content of a document."""
    try:
        return store.get(id).content
    except DocumentNotFoundError as exc:
        raise ValueError(str(exc))


@mcp.tool()
def replace_document(id: str, content: str) -> dict:
    """Replace the full content of a document. Returns id and new length."""
    try:
        doc = store.replace(id, content)
        return {"id": doc.id, "length": len(doc.content)}
    except DocumentNotFoundError as exc:
        raise ValueError(str(exc))


@mcp.tool()
def append_document(id: str, content: str) -> dict:
    """Append text to a document. Returns id and new length."""
    try:
        doc = store.append(id, content)
        return {"id": doc.id, "length": len(doc.content)}
    except DocumentNotFoundError as exc:
        raise ValueError(str(exc))


# ---------------------------------------------------------------------------
# Resources — one per document, registered at startup
# ---------------------------------------------------------------------------

def _register_resources() -> None:
    for doc in store.list():
        doc_id = doc.id
        mime = doc.mime_type

        def make_fn(d_id: str):
            def resource_fn() -> str:
                try:
                    return store.get(d_id).content
                except DocumentNotFoundError as exc:
                    raise ValueError(str(exc))

            resource_fn.__name__ = f"resource_{d_id.replace('.', '_').replace('-', '_')}"
            resource_fn.__qualname__ = resource_fn.__name__
            return resource_fn

        fn = make_fn(doc_id)
        mcp.resource(
            f"doc://{doc_id}",
            name=doc_id,
            description=f"Document: {doc_id}",
            mime_type=mime,
        )(fn)


_register_resources()


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

@mcp.prompt()
def summarize(doc_id: str) -> list[types.PromptMessage]:
    """Summarize a document."""
    try:
        content = store.get(doc_id).content
    except DocumentNotFoundError as exc:
        raise ValueError(str(exc))
    return [
        types.PromptMessage(
            role="user",
            content=types.TextContent(
                type="text",
                text=(
                    f"Please write a concise summary of the following document '{doc_id}':\n\n"
                    f"{content}"
                ),
            ),
        )
    ]


@mcp.prompt()
def improve(doc_id: str, tone: str = "neutral") -> list[types.PromptMessage]:
    """Suggest writing improvements for a document."""
    try:
        content = store.get(doc_id).content
    except DocumentNotFoundError as exc:
        raise ValueError(str(exc))
    return [
        types.PromptMessage(
            role="user",
            content=types.TextContent(
                type="text",
                text=(
                    f"Please suggest writing improvements for the document '{doc_id}' "
                    f"using a {tone} tone. Focus on clarity, structure, and readability.\n\n"
                    f"{content}"
                ),
            ),
        )
    ]


@mcp.prompt()
def grammar(doc_id: str) -> list[types.PromptMessage]:
    """Check and correct grammar in a document."""
    try:
        content = store.get(doc_id).content
    except DocumentNotFoundError as exc:
        raise ValueError(str(exc))
    return [
        types.PromptMessage(
            role="user",
            content=types.TextContent(
                type="text",
                text=(
                    f"Please identify and correct any grammar issues in the document '{doc_id}'. "
                    f"List each issue found and provide the corrected version.\n\n"
                    f"{content}"
                ),
            ),
        )
    ]
