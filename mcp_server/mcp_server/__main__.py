import os
from .app import mcp

port = int(os.environ.get("PORT", "8000"))
mcp.run(transport="streamable-http", host="0.0.0.0", port=port)
