FROM python:3.11-slim

WORKDIR /app

# phm-lite-check core is stdlib-only; the MCP transport layer needs the mcp SDK
RUN pip install --no-cache-dir "mcp>=1.2" && \
    pip install --no-cache-dir "phm-lite-check @ git+https://github.com/PHM-Audit/phm-lite-check@v1.0.1"

# MCP stdio server: starts and responds to initialize/introspection over stdin/stdout
ENTRYPOINT ["python", "-m", "phm_lite_check.mcp_server"]
