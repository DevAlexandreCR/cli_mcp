import os
import sys

DEFAULT_MODEL = "claude-haiku-4-5-20251001"
DEFAULT_MCP_URL = "http://mcp-server:8000/mcp"


class Config:
    def __init__(self, api_key: str, model: str, mcp_server_url: str) -> None:
        self.api_key = api_key
        self.model = model
        self.mcp_server_url = mcp_server_url

    @classmethod
    def from_env(cls) -> "Config":
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
        if not api_key:
            print("Error: ANTHROPIC_API_KEY is not set.", file=sys.stderr)
            sys.exit(1)
        return cls(
            api_key=api_key,
            model=os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL),
            mcp_server_url=os.environ.get("MCP_SERVER_URL", DEFAULT_MCP_URL),
        )
