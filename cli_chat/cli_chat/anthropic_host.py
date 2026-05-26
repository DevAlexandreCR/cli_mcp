import logging

import anthropic
from mcp import ClientSession

from .config import Config
from .mcp_client import call_tool

log = logging.getLogger("anthropic_host")


def _mcp_tools_to_anthropic(mcp_tools: list) -> list[dict]:
    """Convert MCP Tool objects to Anthropic tool schema dicts."""
    result = []
    for t in mcp_tools:
        result.append({
            "name": t.name,
            "description": t.description or "",
            "input_schema": t.inputSchema,
        })
    return result


async def run_chat_turn(
    messages: list,
    mcp_tools: list,
    session: ClientSession,
    config: Config,
) -> str:
    """Send messages to Claude, execute any tool_use blocks via MCP, return final text."""
    client = anthropic.AsyncAnthropic(api_key=config.api_key)
    anthropic_tools = _mcp_tools_to_anthropic(mcp_tools)

    working_messages = list(messages)

    while True:
        log.info(
            "→ Anthropic API | model=%s messages=%d tools=%d",
            config.model,
            len(working_messages),
            len(anthropic_tools),
        )
        response = await client.messages.create(
            model=config.model,
            max_tokens=4096,
            tools=anthropic_tools,
            messages=working_messages,
        )
        log.info("← stop_reason=%s", response.stop_reason)

        if response.stop_reason != "tool_use":
            for block in response.content:
                if hasattr(block, "text"):
                    return block.text
            return ""

        # Append assistant turn with tool_use blocks
        working_messages.append({"role": "assistant", "content": response.content})

        # Execute every tool_use block and collect results
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue

            log.info("tool_use: %s(%s)", block.name, block.input)
            text, is_error = await call_tool(session, block.name, block.input or {})

            if is_error:
                print(f"[tool error: {text}]")

            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": text,
                **({"is_error": True} if is_error else {}),
            })

        working_messages.append({"role": "user", "content": tool_results})
