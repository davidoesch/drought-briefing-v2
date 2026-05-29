FROM ghcr.io/astral-sh/uv:python3.12-bookworm

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangoft2-1.0-0 \
    libharfbuzz0b \
    libfontconfig1 \
    libcairo2 \
    libgdk-pixbuf2.0-0 \
    chromium \
 && rm -rf /var/lib/apt/lists/*

ENV UV_PROJECT_ENVIRONMENT=/venv
ENV UV_HTTP_TIMEOUT=120
ENV CHROME_PATH=/usr/bin/chromium

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY . .
RUN uv sync --frozen
