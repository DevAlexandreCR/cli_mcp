import logging
import sys
from contextlib import asynccontextmanager

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

log = logging.getLogger("mcp_client")


@asynccontextmanager
async def open_mcp_session(url: str):
    """Async context manager that yields a connected, initialized ClientSession."""
    try:
        async with streamablehttp_client(url) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                log.info("MCP session initialized: %s", url)
                yield session
    except Exception as exc:
        print(f"Error: cannot connect to MCP server at {url}: {exc}", file=sys.stderr)
        sys.exit(1)


async def list_tools(session: ClientSession) -> list:
    result = await session.list_tools()
    log.debug("list_tools → %d tools", len(result.tools))
    return result.tools


async def call_tool(session: ClientSession, name: str, arguments: dict) -> tuple[str, bool]:
    """Call an MCP tool. Returns (text_output, is_error)."""
    log.info("call_tool: %s(%s)", name, arguments)
    result = await session.call_tool(name, arguments)
    text = "\n".join(
        item.text for item in result.content if hasattr(item, "text")
    )
    return text, result.isError


async def list_resources(session: ClientSession) -> list:
    result = await session.list_resources()
    log.debug("list_resources → %d resources", len(result.resources))
    return result.resources


async def read_resource(session: ClientSession, uri: str) -> str:
    log.info("read_resource: %s", uri)
    result = await session.read_resource(uri)  # type: ignore[arg-type]
    return "\n".join(
        item.text for item in result.contents if hasattr(item, "text")
    )


async def list_prompts(session: ClientSession) -> list:
    result = await session.list_prompts()
    log.debug("list_prompts → %d prompts", len(result.prompts))
    return result.prompts


async def get_prompt(session: ClientSession, name: str, arguments: dict) -> list:
    """Return list of PromptMessage objects."""
    log.info("get_prompt: %s(%s)", name, arguments)
    result = await session.get_prompt(name, arguments)
    return result.messages
