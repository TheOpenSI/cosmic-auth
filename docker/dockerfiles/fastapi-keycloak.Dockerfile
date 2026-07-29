FROM ghcr.io/astral-sh/uv:python3.14-trixie AS base
WORKDIR /app

FROM base AS dev_platform
COPY ./ ./
RUN uv sync --frozen --no-cache

ENV PYTHONPATH=/
EXPOSE 8081/tcp
CMD ["uv", "run", "uvicorn", "app.auth.main:app", "--host", "0.0.0.0", "--port", "8081", "--reload"]