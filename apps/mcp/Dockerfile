# Cyber Task Hub MCP sunucusu imajı (HTTP modu, ADR-0003)
# Kimlik istemcinin `Authorization: Bearer <API token>` başlığından gelir; imajda token yoktur.
FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy
RUN pip install --no-cache-dir uv==0.13.9
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY cth_mcp ./cth_mcp
RUN uv sync --frozen --no-dev
ENV PATH="/app/.venv/bin:$PATH" \
    CTH_MCP_TRANSPORT=http \
    CTH_MCP_HOST=0.0.0.0 \
    CTH_MCP_PORT=8001
RUN useradd --system --uid 10001 cth && chown -R cth /app
USER cth
EXPOSE 8001
HEALTHCHECK --interval=5s --retries=20 CMD ["python", "-c", "import socket; socket.create_connection(('127.0.0.1', 8001), timeout=2).close()"]
CMD ["cth-mcp"]
