# Docker Compose Dev Stack — Design Spec

**Date:** 2026-05-28
**Status:** Approved

## Problem

The project deploys as a stlite (serverless/WASM) app to GitHub Pages. The only way to see UI/UX changes is to push to GitHub and wait for the Pages deploy. This creates a slow, expensive feedback loop for frontend iteration.

## Goal

A `docker compose up` command that starts a real Streamlit server locally with hot reload, so UI changes are visible in the browser within seconds. A `make run-tests` command that runs the pytest suite in the same container environment.

## Architecture

One `Dockerfile` shared by both Compose services. Python venv is installed at `/venv` (not `/app/.venv`) so the bind-mounted source directory doesn't shadow installed packages.

**Files added:**
- `Dockerfile`
- `docker-compose.yml`
- `.dockerignore`
- `Makefile`

## Dockerfile

Base image: `ghcr.io/astral-sh/uv:python3.12-bookworm` — mirrors the local `uv` workflow and locks to the same `uv.lock`.

System packages required:
- **WeasyPrint** (PDF export): `libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz0b libfontconfig1 libcairo2 libgdk-pixbuf2.0-0`
- **kaleido/choreographer** (chart PNG export): `chromium`

Dependency install strategy (two-step for layer caching):
1. Copy `pyproject.toml` + `uv.lock`, run `uv sync --frozen --no-install-project` — installs all third-party deps
2. Copy source, run `uv sync --frozen` — installs the project itself

`UV_PROJECT_ENVIRONMENT=/venv` isolates the venv from the `/app` bind mount.

## docker-compose.yml

### `app` service
- Port `8501:8501`
- Bind mount `.:/app` for hot reload
- Streamlit flags: `--server.runOnSave=true --server.fileWatcherType=watchdog`
- `UV_PROJECT_ENVIRONMENT=/venv`

### `test` service
- Same image, same bind mount
- Command: `uv run pytest tests/ -v`
- One-shot (run with `docker compose run --rm test`)

## Makefile Targets

| Target | Command | Purpose |
|--------|---------|---------|
| `make build` | `docker compose build` | Build/rebuild image |
| `make up` | `docker compose up app` | Start dev server |
| `make down` | `docker compose down` | Stop all services |
| `make run-tests` | `docker compose run --rm test` | Run pytest suite |
| `make shell` | `docker compose run --rm app bash` | Drop into container shell |

## Known Risk: Chromium Path for kaleido

kaleido 1.3.0 uses `choreographer` to drive a Chrome binary for chart PNG export. On Debian bookworm, `chromium` installs to `/usr/bin/chromium`. choreographer may auto-detect it or require `CHROME_PATH=/usr/bin/chromium`. This must be verified during implementation — add the env var to both services if auto-detection fails.

## Out of Scope

- Production/deployment Docker image (project deploys as stlite to GitHub Pages)
- Multi-stage production build
- CI/CD Docker integration
