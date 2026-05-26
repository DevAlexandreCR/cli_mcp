"""
Parses user input to identify special prefixes and @resource tokens.

Recognized patterns:
  /            → bare slash (list prompts)
  /<name> ...  → prompt invocation (name is first token after /)
  @            → bare at (list resources)
  text with @<id> tokens → message with inline resource references
"""
import re
from dataclasses import dataclass
from enum import Enum, auto


class InputType(Enum):
    BARE_SLASH = auto()    # single "/"
    PROMPT = auto()        # "/<name>" with optional args
    BARE_AT = auto()       # single "@"
    MESSAGE = auto()       # anything else (may contain @<id> tokens)


@dataclass
class ParsedInput:
    type: InputType
    raw: str
    # For PROMPT: prompt name and trailing text (space-sep args)
    prompt_name: str = ""
    prompt_args_raw: str = ""
    # For MESSAGE: whether it contains @tokens
    has_at_tokens: bool = False


_AT_TOKEN_RE = re.compile(r"@(\S+)")


def parse_input(raw: str) -> ParsedInput:
    stripped = raw.strip()

    if stripped == "/":
        return ParsedInput(type=InputType.BARE_SLASH, raw=stripped)

    if stripped.startswith("/"):
        parts = stripped[1:].split(maxsplit=1)
        name = parts[0]
        args_raw = parts[1] if len(parts) > 1 else ""
        return ParsedInput(
            type=InputType.PROMPT,
            raw=stripped,
            prompt_name=name,
            prompt_args_raw=args_raw,
        )

    if stripped == "@":
        return ParsedInput(type=InputType.BARE_AT, raw=stripped)

    has_at = bool(_AT_TOKEN_RE.search(stripped))
    return ParsedInput(type=InputType.MESSAGE, raw=stripped, has_at_tokens=has_at)


def extract_at_tokens(text: str) -> list[str]:
    """Return all @<id> values found in text (without the @ prefix)."""
    return _AT_TOKEN_RE.findall(text)


def replace_at_token(text: str, token_id: str, replacement: str) -> str:
    """Replace @<token_id> with replacement in text."""
    return text.replace(f"@{token_id}", replacement, 1)
