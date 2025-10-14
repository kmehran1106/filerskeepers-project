# Build stage
FROM python:3.13.5-slim-bullseye AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt-get update && apt-get install --no-install-recommends -y \
  gcc \
  python3-dev \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app/src
ENV UV_PROJECT_ENVIRONMENT=.dockervenv
COPY ./pyproject.toml ./uv.lock ./
RUN uv sync --frozen

# Production stage
FROM python:3.13.5-slim-bullseye AS prod
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
COPY --from=builder /app/src/.dockervenv /app/src/.dockervenv
WORKDIR /app/src

COPY . .
