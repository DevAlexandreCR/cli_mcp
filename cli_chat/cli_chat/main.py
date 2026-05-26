import asyncio
import logging
import sys

from mcp import ClientSession

from .anthropic_host import run_chat_turn
from .config import Config
from .input_parser import (
    InputType,
    extract_at_tokens,
    parse_input,
    replace_at_token,
)
from .mcp_client import (
    get_prompt,
    list_prompts,
    list_resources,
    list_tools,
    open_mcp_session,
    read_resource,
)


def _setup_logging() -> None:
    level_name = __import__("os").environ.get("LOG_LEVEL", "WARNING").upper()
    level = getattr(logging, level_name, logging.WARNING)
    fmt = "%(name)s | %(levelname)s | %(message)s"
    logging.basicConfig(stream=sys.stderr, level=level, format=fmt)


def _banner(config: Config) -> None:
    print("=" * 60)
    print("  MCP Doc Chat")
    print(f"  Server : {config.mcp_server_url}")
    print(f"  Model  : {config.model}")
    print("  Store  : in-memory — restarts wipe edits")
    print("  Type / to list prompts, @ to list resources")
    print("  Ctrl+C or Ctrl+D to quit")
    print("=" * 60)
    print()


# ---------------------------------------------------------------------------
# / prompt handling
# ---------------------------------------------------------------------------

async def _handle_bare_slash(session: ClientSession) -> None:
    prompts = await list_prompts(session)
    if not prompts:
        print("(no prompts available)")
        return
    print("Available prompts:")
    for p in prompts:
        desc = p.description or ""
        args = ", ".join(
            f"{a.name}{'?' if not a.required else ''}"
            for a in (p.arguments or [])
        )
        print(f"  /{p.name}  {f'({args})' if args else ''}  {desc}")


async def _handle_prompt_command(
    prompt_name: str,
    args_raw: str,
    session: ClientSession,
    messages: list,
) -> bool:
    """Resolve a /name command, inject messages into conversation. Returns True on success."""
    prompts = await list_prompts(session)
    prompt_def = next((p for p in prompts if p.name == prompt_name), None)
    if prompt_def is None:
        print(f"Unknown prompt: /{prompt_name}")
        return False

    # Collect required arguments interactively
    arguments: dict[str, str] = {}
    for arg in prompt_def.arguments or []:
        if arg.required:
            # Check if value was supplied inline (positional after name)
            if args_raw:
                arguments[arg.name] = args_raw
                args_raw = ""
            else:
                try:
                    val = await asyncio.to_thread(input, f"  {arg.name}: ")
                except (EOFError, KeyboardInterrupt):
                    print()
                    return False
                arguments[arg.name] = val.strip()
        else:
            # Optional — only prompt if not a tone-style shorthand
            try:
                val = await asyncio.to_thread(
                    input, f"  {arg.name} (optional, Enter to skip): "
                )
            except (EOFError, KeyboardInterrupt):
                print()
                break
            if val.strip():
                arguments[arg.name] = val.strip()

    prompt_messages = await get_prompt(session, prompt_name, arguments)
    # Convert PromptMessage objects to Anthropic message dicts
    for pm in prompt_messages:
        content = pm.content.text if hasattr(pm.content, "text") else str(pm.content)
        messages.append({"role": pm.role, "content": content})
    return True


# ---------------------------------------------------------------------------
# @ resource handling
# ---------------------------------------------------------------------------

async def _handle_bare_at(session: ClientSession) -> None:
    resources = await list_resources(session)
    if not resources:
        print("(no resources available)")
        return
    print("Available resources:")
    for r in resources:
        print(f"  @{r.name}  [{r.mimeType}]  {r.uri}")


async def _expand_at_tokens(text: str, session: ClientSession) -> str | None:
    """Replace @<id> tokens with inlined resource content. Returns None on error."""
    token_ids = extract_at_tokens(text)
    resources = await list_resources(session)
    resource_map = {r.name: str(r.uri) for r in resources}

    expanded = text
    for token_id in token_ids:
        if token_id not in resource_map:
            print(f"Unknown resource: @{token_id}")
            return None
        uri = resource_map[token_id]
        content = await read_resource(session, uri)
        block = f"\n--- doc://{token_id} ---\n{content}\n--- end ---\n"
        expanded = replace_at_token(expanded, token_id, block)
    return expanded


# ---------------------------------------------------------------------------
# Main chat loop
# ---------------------------------------------------------------------------

async def chat_loop(session: ClientSession, config: Config) -> None:
    mcp_tools = await list_tools(session)
    messages: list[dict] = []

    while True:
        try:
            raw = await asyncio.to_thread(input, "you> ")
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            return

        raw = raw.strip()
        if not raw:
            continue

        parsed = parse_input(raw)

        if parsed.type == InputType.BARE_SLASH:
            await _handle_bare_slash(session)
            continue

        if parsed.type == InputType.PROMPT:
            ok = await _handle_prompt_command(
                parsed.prompt_name, parsed.prompt_args_raw, session, messages
            )
            if not ok:
                continue
            # messages already has the prompt content; fall through to Claude

        elif parsed.type == InputType.BARE_AT:
            await _handle_bare_at(session)
            continue

        else:
            # Regular message — expand any @tokens
            expanded = await _expand_at_tokens(raw, session)
            if expanded is None:
                continue
            messages.append({"role": "user", "content": expanded})

        # Send to Claude (with tool-use loop inside run_chat_turn)
        print()
        reply = await run_chat_turn(messages, mcp_tools, session, config)
        print(f"assistant> {reply}")
        print()
        messages.append({"role": "assistant", "content": reply})


async def _run() -> None:
    _setup_logging()
    config = Config.from_env()
    _banner(config)

    async with open_mcp_session(config.mcp_server_url) as session:
        await chat_loop(session, config)


def main() -> None:
    asyncio.run(_run())
