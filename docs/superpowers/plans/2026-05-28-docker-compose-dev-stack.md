# Docker Compose Dev Stack Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `Dockerfile`, `docker-compose.yml`, `.dockerignore`, and `Makefile` so developers can run the Streamlit app locally with hot reload (`make up`) and run the pytest suite in a container (`make run-tests`), eliminating the need to push to GitHub to see UI changes.

**Architecture:** One shared `Dockerfile` based on `ghcr.io/astral-sh/uv:python3.12-bookworm`. Python deps are installed into `/venv` (not `/app/.venv`) so the source bind-mount doesn't shadow installed packages. Two Compose services: `app` (Streamlit hot-reload on port 8501) and `test` (pytest one-shot). Makefile wraps all commands.

**Tech Stack:** Docker, Docker Compose v2, uv 0.x, Streamlit 1.57, pytest 9, WeasyPrint 68, kaleido 1.3 / choreographer

---

## File Map

| File | Action | Responsibility |
|------|--------|----------------|
| `.dockerignore` | Create | Exclude `.venv/`, `__pycache__`, `.git`, `.pytest_cache` from build context |
| `Dockerfile` | Create | Build image: system deps + uv sync into `/venv` |
| `docker-compose.yml` | Create | `app` (Streamlit) and `test` (pytest) services |
| `Makefile` | Create | Developer-facing commands: `build`, `up`, `down`, `run-tests`, `shell` |

---

### Task 1: Add .dockerignore

**Files:**
- Create: `.dockerignore`

- [ ] **Step 1: Create `.dockerignore`**

```
.venv/
__pycache__/
*.pyc
*.pyo
.git/
.pytest_cache/
docs/
*.md
```

- [ ] **Step 2: Commit**

```bash
git add .dockerignore
git commit -m "chore: add .dockerignore for Docker build context"
```

---

### Task 2: Write Dockerfile and verify it builds

**Files:**
- Create: `Dockerfile`

- [ ] **Step 1: Write `Dockerfile`**

```dockerfile
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
ENV CHROME_PATH=/usr/bin/chromium

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY . .
RUN uv sync --frozen
```

- [ ] **Step 2: Build the image**

```bash
docker build -t drought-briefing .
```

Expected: build succeeds, ends with a layer hash. The first build will take several minutes due to system packages and Python deps. Subsequent builds are fast because apt and uv layers are cached.

- [ ] **Step 3: Verify Python and key packages are available in the image**

```bash
docker run --rm drought-briefing /venv/bin/python -c "import streamlit, geopandas, weasyprint, kaleido; print('OK')"
```

Expected output: `OK`

If this fails with an import error, the most likely culprit is a missing system library for WeasyPrint. Run `docker run --rm drought-briefing /venv/bin/python -c "import weasyprint"` to isolate, then add the missing `apt` package to the `Dockerfile`.

- [ ] **Step 4: Commit**

```bash
git add Dockerfile
git commit -m "chore: add Dockerfile with uv + system deps for WeasyPrint and kaleido"
```

---

### Task 3: Write docker-compose.yml and verify syntax

**Files:**
- Create: `docker-compose.yml`

- [ ] **Step 1: Write `docker-compose.yml`**

```yaml
services:
  app:
    build: .
    ports:
      - "8501:8501"
    volumes:
      - .:/app
    environment:
      UV_PROJECT_ENVIRONMENT: /venv
      CHROME_PATH: /usr/bin/chromium
    command: >
      uv run streamlit run app.py
      --server.port=8501
      --server.address=0.0.0.0
      --server.runOnSave=true
      --server.fileWatcherType=watchdog

  test:
    build: .
    volumes:
      - .:/app
    environment:
      UV_PROJECT_ENVIRONMENT: /venv
      CHROME_PATH: /usr/bin/chromium
    command: uv run pytest tests/ -v
    profiles: [test]
```

- [ ] **Step 2: Validate Compose syntax**

```bash
docker compose config
```

Expected: prints the fully resolved config with no errors.

- [ ] **Step 3: Commit**

```bash
git add docker-compose.yml
git commit -m "chore: add docker-compose.yml with app and test services"
```

---

### Task 4: Write Makefile

**Files:**
- Create: `Makefile`

- [ ] **Step 1: Write `Makefile`**

```makefile
.PHONY: build up down run-tests shell

build:
	docker compose build

up:
	docker compose up app

down:
	docker compose down

run-tests:
	docker compose run --rm test

shell:
	docker compose run --rm app bash
```

**Important:** The indentation in Makefiles must use **tabs**, not spaces. Paste carefully.

- [ ] **Step 2: Verify `make build` runs without error**

```bash
make build
```

Expected: `docker compose build` runs (uses cached layers from Task 2, so very fast).

- [ ] **Step 3: Commit**

```bash
git add Makefile
git commit -m "chore: add Makefile with build/up/down/run-tests/shell targets"
```

---

### Task 5: Verify app service — Streamlit starts and hot reload works

**Files:** None (smoke test only)

- [ ] **Step 1: Start the app service**

```bash
make up
```

Expected: Streamlit starts, terminal shows:

```
  You can now view your Streamlit app in your browser.
  URL: http://0.0.0.0:8501
```

- [ ] **Step 2: Open the browser**

Navigate to `http://localhost:8501`. The Drought Briefing app should load with the region selector in the sidebar.

- [ ] **Step 3: Verify hot reload**

With `make up` still running, open `app.py` in your editor and add a comment to any line (e.g., `# test`). Save the file. Within 1-2 seconds Streamlit should show "Source file changed. Rerunning..." in the terminal and reload in the browser.

- [ ] **Step 4: Stop the service**

```bash
make down
```

---

### Task 6: Verify test service — all tests pass

**Files:** None (smoke test only)

- [ ] **Step 1: Run the test suite inside the container**

```bash
make run-tests
```

Expected: pytest output ending with something like:

```
=================== X passed in Y.YYs ===================
```

All existing tests should pass. If any fail, the failure is a pre-existing issue unrelated to this Docker setup — investigate separately.

- [ ] **Step 2: Verify the container is removed after the run**

```bash
docker ps -a | grep drought
```

Expected: no stopped containers listed (the `--rm` flag in `docker compose run --rm` removes the container after exit).

---

### Task 7: Verify kaleido chart export works in the container

kaleido 1.3.0 uses `choreographer` to drive a headless Chromium for PNG chart export. This is the highest-risk component — running Chrome headlessly as root in a container requires `--no-sandbox`.

**Files:**
- Modify: `Dockerfile` (add `--no-sandbox` flag if needed)

- [ ] **Step 1: Test kaleido inside the container**

```bash
docker compose run --rm app uv run python -c "
import plotly.graph_objects as go
fig = go.Figure(go.Bar(x=[1,2,3], y=[4,5,6]))
png = fig.to_image(format='png')
print(f'PNG bytes: {len(png)}')
"
```

Expected output: `PNG bytes: <some number above 1000>`

- [ ] **Step 2: If kaleido fails with a sandbox or Chrome-not-found error**

The error will look like: `[Errno 8] Exec format error` or `Failed to launch the browser process`.

Add `--no-sandbox` via the `CHROMIUM_FLAGS` env var in `Dockerfile`:

```dockerfile
ENV CHROME_PATH=/usr/bin/chromium
ENV CHROMIUM_FLAGS="--no-sandbox --disable-dev-shm-usage"
```

Rebuild and retest:

```bash
docker compose build
docker compose run --rm app uv run python -c "
import plotly.graph_objects as go
fig = go.Figure(go.Bar(x=[1,2,3], y=[4,5,6]))
png = fig.to_image(format='png')
print(f'PNG bytes: {len(png)}')
"
```

- [ ] **Step 3: If `CHROMIUM_FLAGS` is not picked up by choreographer**

choreographer may use a different mechanism. Try setting the flag via the kaleido scope config:

```bash
docker compose run --rm app uv run python -c "
import kaleido
# Check what config options are available
print(dir(kaleido))
"
```

If choreographer exposes a `PYPPETEER_ARGS` or similar env var, add it to the `Dockerfile` ENV block. Check choreographer 1.3.0 source at `/venv/lib/python3.12/site-packages/choreographer/` to find the right env var name.

- [ ] **Step 4: Commit if Dockerfile was modified**

```bash
git add Dockerfile
git commit -m "fix: add Chromium no-sandbox flags for kaleido in Docker"
```

---

## Verification Checklist

Before considering this complete:

- [ ] `make build` succeeds from a clean checkout
- [ ] `make up` starts Streamlit at `http://localhost:8501`
- [ ] Editing a `.py` file triggers a Streamlit reload within 2 seconds
- [ ] `make run-tests` runs all tests and they pass
- [ ] `make down` stops the stack cleanly
- [ ] kaleido can produce PNG bytes (Task 7 Step 1 passes)
