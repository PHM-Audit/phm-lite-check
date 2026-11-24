FROM python:3.11-slim

WORKDIR /app

# phm-lite-check core is stdlib-only; the MCP transport layer needs the mcp SDK.
# Pinned to mcp 1.x: the 2.x SDK renamed FastMCP and is incompatible with this server.
RUN pip install --no-cache-dir "mcp>=1.2,<2" && \
    pip install --no-cache-dir "phm-lite-check[mcp]==1.0.3"

# MCP stdio server: starts and responds to initialize/tools over stdin/stdout
ENTRYPOINT ["python", "-m", "phm_lite_check.mcp_server"]
