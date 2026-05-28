# stlite / GitHub Pages Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert the Drought Briefing Streamlit app to run fully in-browser via stlite (Pyodide/WASM) and publish it to GitHub Pages via GitHub Actions CI.

**Architecture:** Replace the three WASM-incompatible features (WeasyPrint PDF, kaleido chart PNG, streamlit-folium component) with browser-compatible equivalents, create a stlite `index.html` mount page, and add a GitHub Actions workflow that assembles and deploys the static site on every push to `main`.

**Tech Stack:** stlite (`@stlite/mountable` via jsDelivr CDN), Pyodide, GitHub Actions (`actions/upload-pages-artifact`, `actions/deploy-pages`), Python 3.12, uv

---

## Files Changed / Created

| File | Action | Reason |
|------|--------|--------|
| `src/export/report.py` | Modify | Replace kaleido PNG with Plotly inline HTML |
| `app.py` | Modify | Replace `st_folium` + PDF export with WASM-compatible equivalents |
| `pyproject.toml` | Modify | Remove 5 WASM-incompatible dependencies |
| `docs/index.html` | Create | stlite mount page served by GitHub Pages |
| `.github/workflows/deploy.yml` | Create | CI workflow to assemble and deploy the static site |
| `tests/test_export.py` | Create | Verify new `to_html()` embeds Plotly, not PNG |

---

## Task 1: Update `src/export/report.py` — embed Plotly HTML instead of kaleido PNG

**Files:**
- Modify: `src/export/report.py`
- Create: `tests/test_export.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_export.py`:

```python
import plotly.graph_objects as go

from src.aggregation.regional import compute_region_report
from src.briefing.template import build_briefing
from src.data.fixture_loader import load
from src.export.report import to_html


def test_to_html_embeds_plotly_not_png():
    bundle = load()
    report = compute_region_report(34, bundle)
    doc = build_briefing(report, "behoerden")
    fig = go.Figure(go.Scatter(x=[1, 2], y=[1, 2]))

    html = to_html(doc, report, chart_fig=fig, map_png=None)

    assert "plotly" in html.lower(), "Plotly JS must be embedded inline"
    assert "data:image/png;base64" not in html, "No kaleido PNG blobs expected"
    assert "<!DOCTYPE html>" in html


def test_to_html_without_chart_is_valid():
    bundle = load()
    report = compute_region_report(34, bundle)
    doc = build_briefing(report, "behoerden")

    html = to_html(doc, report, chart_fig=None, map_png=None)

    assert "<!DOCTYPE html>" in html
    assert "plotly" not in html.lower(), "No Plotly when chart_fig is None"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_export.py -v
```

Expected: FAIL — `assert "plotly" in html.lower()` fails because the current implementation embeds a PNG.

- [ ] **Step 3: Replace `_chart_to_png_b64` with Plotly HTML in `src/export/report.py`**

Delete the `_chart_to_png_b64` function and update the chart block inside `to_html()`. The full updated file:

```python
# src/export/report.py
from __future__ import annotations

import base64

import plotly.io as pio

from config.settings import CDI_COLOURS, CDI_LABELS
from src.models import BriefingDocument, RegionReport


def _map_to_b64(png_bytes: bytes) -> str:
    return base64.b64encode(png_bytes).decode()


_CSS = """
body { font-family: 'Helvetica Neue', Arial, sans-serif; background: #fff; color: #1a1a2e; margin: 0; padding: 0; }
.page { max-width: 800px; margin: 0 auto; padding: 32px; }
h1 { font-size: 22px; color: #1a1a2e; margin-bottom: 4px; }
.subtitle { color: #555; font-size: 13px; margin-bottom: 24px; }
.cdi-badge { display: inline-block; padding: 6px 18px; border-radius: 6px; font-size: 28px;
             font-weight: bold; color: white; margin-bottom: 20px; }
.indicators { display: flex; gap: 16px; margin-bottom: 24px; }
.indicator { flex: 1; border: 1px solid #ddd; border-radius: 8px; padding: 12px; text-align: center; }
.indicator .label { font-size: 10px; color: #888; text-transform: uppercase; }
.indicator .value { font-size: 22px; font-weight: bold; color: #1a1a2e; }
.indicator .delta { font-size: 11px; color: #888; }
.section { margin-bottom: 20px; }
.section h2 { font-size: 12px; text-transform: uppercase; letter-spacing: 1px; color: #888; margin-bottom: 6px; }
.section p { font-size: 13px; line-height: 1.7; color: #333; margin: 0; }
.visuals { display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }
.visual-box { flex: 1; min-width: 300px; }
.visual-box img { width: 100%; border-radius: 8px; }
.quality-bar { background: #f5f5f5; border-radius: 6px; padding: 10px 16px;
               font-size: 11px; color: #666; margin-top: 24px; }
.quality-bar strong { color: #333; }
"""


def to_html(
    doc: BriefingDocument,
    report: RegionReport,
    chart_fig=None,
    map_png: bytes | None = None,
) -> str:
    cdi_colour = CDI_COLOURS.get(report.cdi, "#cccccc")
    cdi_label = CDI_LABELS.get(report.cdi, "Unbekannt")
    mode_label = "Behoerdenbriefing" if doc.mode == "behoerden" else "Mein Trockenheitsbulletin"

    def fmt(v, fmt_str=".1f", fallback="--"):
        try:
            return format(v, fmt_str)
        except Exception:
            return fallback

    def delta_arrow(v):
        if v > 0:
            return f"+{v:.2f}"
        if v < 0:
            return f"-{abs(v):.2f}"
        return "0.00"

    chart_html = ""
    if chart_fig is not None:
        chart_html = pio.to_html(chart_fig, full_html=False, include_plotlyjs="inline")

    map_html = ""
    if map_png is not None:
        b64 = _map_to_b64(map_png)
        map_html = f'<img src="data:image/png;base64,{b64}" alt="CDI-Karte">'

    quality_colour = {"ok": "#2ecc71", "warning": "#f1c40f", "error": "#e74c3c"}.get(
        report.quality.overall, "#ccc"
    )

    html = f"""<!DOCTYPE html>
<html lang="de">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{mode_label}: {report.region_name_de}</title>
<style>{_CSS}</style>
</head>
<body>
<div class="page">
  <h1>{mode_label}: Trockenheit - {report.region_name_de}</h1>
  <div class="subtitle">Kanton Bern - Datenstand: {report.data_timestamp.strftime("%d.%m.%Y")} - Quelle: {report.source}</div>

  <div class="cdi-badge" style="background:{cdi_colour}">CDI {report.cdi} - {cdi_label}</div>

  <div class="indicators">
    <div class="indicator">
      <div class="label">SPI-3m</div>
      <div class="value">{fmt(report.spi_3m, ".2f")}</div>
      <div class="delta">{delta_arrow(report.spi_3m_delta)}/Woche</div>
    </div>
    <div class="indicator">
      <div class="label">Bodenfeuchte</div>
      <div class="value">{fmt(report.soil_moisture_pct, ".0f")}%</div>
      <div class="delta">nFK - {report.spi_3m_percentile}. Perz.</div>
    </div>
    <div class="indicator">
      <div class="label">VHI</div>
      <div class="value">{fmt(report.vhi, ".1f")}</div>
      <div class="delta">{delta_arrow(report.vhi_delta)}</div>
    </div>
    <div class="indicator">
      <div class="label">% krit. Wochen</div>
      <div class="value">{report.pct_critical * 100:.0f}%</div>
      <div class="delta">letzte 52 Wochen</div>
    </div>
  </div>

  <div class="visuals">
    <div class="visual-box">{map_html}</div>
    <div class="visual-box">{chart_html}</div>
  </div>

  <div class="section">
    <h2>Lage</h2>
    <p>{doc.sections["lage"]}</p>
  </div>
  <div class="section">
    <h2>Entwicklung</h2>
    <p>{doc.sections["entwicklung"]}</p>
  </div>
  <div class="section">
    <h2>Einordnung</h2>
    <p>{doc.sections["einordnung"]}</p>
  </div>
  <div class="section">
    <h2>Datengrundlage</h2>
    <p>{doc.sections["datengrundlage"]}</p>
  </div>

  <div class="quality-bar">
    <strong>Qualitaet:</strong>
    <span style="color:{quality_colour}">● {report.quality.overall.upper()}</span>
    &nbsp;|&nbsp; Aktualitaet: {report.quality.data_age_days} Tage
    &nbsp;|&nbsp; Abdeckung: {report.quality.coverage_pct:.0%}
    {(" &nbsp;|&nbsp; Ausreisser: " + ", ".join(report.quality.outlier_flags)) if report.quality.outlier_flags else ""}
    {(" &nbsp;|&nbsp; Fehlend: " + ", ".join(report.quality.missing_columns)) if report.quality.missing_columns else ""}
  </div>
</div>
</body>
</html>"""
    return html
```

Note: `to_pdf()` is deleted entirely — it is no longer called anywhere.

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_export.py -v
```

Expected: both tests PASS.

- [ ] **Step 5: Run the full test suite to check for regressions**

```bash
uv run pytest tests/ -v
```

Expected: all existing tests PASS.

- [ ] **Step 6: Commit**

```bash
git add src/export/report.py tests/test_export.py
git commit -m "feat: replace kaleido chart PNG with inline Plotly HTML in HTML export"
```

---

## Task 2: Update `app.py` — replace st_folium and PDF export

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Replace the three incompatible sections in `app.py`**

Apply these three changes:

**Change A — imports (lines 7–8):** Remove `streamlit_folium` and `to_pdf`.

```python
# Remove this line entirely:
from streamlit_folium import st_folium

# Change this line:
from src.export.report import to_html, to_pdf
# To:
from src.export.report import to_html
```

**Change B — map rendering (around line 113):** Replace `st_folium` call.

```python
# Before:
st_folium(folium_map, width=None, height=300, returned_objects=[])

# After:
st.components.v1.html(folium_map._repr_html_(), height=300)
```

**Change C — export placeholder (lines 143–158):** Remove PDF button, add print note, guard `build_export_map`.

```python
# Before:
with export_placeholder:
    map_png = build_export_map(report, all_reports)
    html_str = to_html(doc, report, chart_fig=fig, map_png=map_png)

    st.download_button(
        label="⬇ PDF exportieren",
        data=to_pdf(html_str),
        file_name=f"trockenheit_{report.region_name_de.replace(' ', '_')}_{report.data_timestamp.strftime('%Y%m%d')}.pdf",
        mime="application/pdf",
    )
    st.download_button(
        label="⬇ HTML exportieren",
        data=html_str.encode("utf-8"),
        file_name=f"trockenheit_{report.region_name_de.replace(' ', '_')}_{report.data_timestamp.strftime('%Y%m%d')}.html",
        mime="text/html",
    )

# After:
with export_placeholder:
    try:
        map_png = build_export_map(report, all_reports)
    except Exception:
        map_png = None
    html_str = to_html(doc, report, chart_fig=fig, map_png=map_png)

    st.info("💡 PDF: Datei → Drucken → Als PDF speichern (Ctrl+P)")
    st.download_button(
        label="⬇ HTML exportieren",
        data=html_str.encode("utf-8"),
        file_name=f"trockenheit_{report.region_name_de.replace(' ', '_')}_{report.data_timestamp.strftime('%Y%m%d')}.html",
        mime="text/html",
    )
```

- [ ] **Step 2: Run the full test suite**

```bash
uv run pytest tests/ -v
```

Expected: all tests PASS (no test directly exercises `app.py` UI, so no regressions expected).

- [ ] **Step 3: Smoke-test the local app**

```bash
uv run streamlit run app.py
```

Open `http://localhost:8501` in a browser. Verify:
- The CDI map renders (now as folium HTML in an iframe component)
- The Plotly timeseries chart renders
- The "HTML exportieren" download button works and the downloaded file opens correctly in a browser
- The PDF button is gone; the `st.info` print note is visible in the sidebar
- No Python errors in the terminal

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "feat: replace st_folium and PDF export for stlite compatibility"
```

---

## Task 3: Remove WASM-incompatible dependencies from `pyproject.toml`

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Remove the five packages**

In `pyproject.toml`, remove these lines from the `dependencies` list:

```toml
# Remove:
"folium>=0.20.0",        # KEEP — folium is used and works in Pyodide
"kaleido>=1.3.0",        # REMOVE — Chromium binary, no WASM build
"pystac-client>=0.9.0",  # REMOVE — unused at runtime
"requests>=2.34.2",      # REMOVE — unused at runtime
"streamlit-folium>=0.27.2",  # REMOVE — requires live server
"weasyprint>=68.1",      # REMOVE — Cairo C library, no WASM build
```

> Note: `folium` stays. Only remove `kaleido`, `pystac-client`, `requests`, `streamlit-folium`, `weasyprint`.

The resulting `dependencies` block should be:

```toml
dependencies = [
    "folium>=0.20.0",
    "geopandas>=1.1.3",
    "matplotlib>=3.10.9",
    "pandas>=3.0.3",
    "plotly>=6.7.0",
    "pypdf>=6.12.2",
    "shapely>=2.1.2",
    "streamlit>=1.57.0",
]
```

- [ ] **Step 2: Sync the environment**

```bash
uv sync
```

Expected: uv removes the unneeded packages with no errors. No import errors should appear.

- [ ] **Step 3: Verify the app still starts**

```bash
uv run streamlit run app.py
```

Expected: app starts and runs without ImportError.

- [ ] **Step 4: Run the full test suite**

```bash
uv run pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: remove WASM-incompatible dependencies (kaleido, weasyprint, streamlit-folium, pystac-client, requests)"
```

---

## Task 4: Create `docs/index.html` — stlite mount page

**Files:**
- Create: `docs/index.html`

- [ ] **Step 1: Verify the latest stlite version**

Go to `https://www.jsdelivr.com/package/npm/@stlite/mountable` and note the latest version number. Substitute it for `0.73.0` in the file below if a newer version exists.

- [ ] **Step 2: Create `docs/index.html`**

```html
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Trockenheitsbriefing Kanton Bern</title>
  <link
    rel="stylesheet"
    href="https://cdn.jsdelivr.net/npm/@stlite/mountable@0.73.0/build/stlite.css"
  />
</head>
<body>
  <div id="root"></div>
  <script src="https://cdn.jsdelivr.net/npm/@stlite/mountable@0.73.0/build/stlite.js"></script>
  <script>
    stlite.mount(
      {
        requirements: [
          "pandas",
          "plotly",
          "geopandas",
          "matplotlib",
          "folium",
        ],
        entrypoint: "app.py",
        files: {
          "app.py":                         { url: "./app.py" },
          "config/__init__.py":             { url: "./config/__init__.py" },
          "config/settings.py":             { url: "./config/settings.py" },
          "src/__init__.py":                { url: "./src/__init__.py" },
          "src/models.py":                  { url: "./src/models.py" },
          "src/aggregation/__init__.py":    { url: "./src/aggregation/__init__.py" },
          "src/aggregation/indicators.py":  { url: "./src/aggregation/indicators.py" },
          "src/aggregation/regional.py":    { url: "./src/aggregation/regional.py" },
          "src/briefing/__init__.py":       { url: "./src/briefing/__init__.py" },
          "src/briefing/template.py":       { url: "./src/briefing/template.py" },
          "src/briefing/text_blocks.py":    { url: "./src/briefing/text_blocks.py" },
          "src/data/__init__.py":           { url: "./src/data/__init__.py" },
          "src/data/fixture_loader.py":     { url: "./src/data/fixture_loader.py" },
          "src/data/stac_client.py":        { url: "./src/data/stac_client.py" },
          "src/export/__init__.py":         { url: "./src/export/__init__.py" },
          "src/export/report.py":           { url: "./src/export/report.py" },
          "src/quality/__init__.py":        { url: "./src/quality/__init__.py" },
          "src/quality/checks.py":          { url: "./src/quality/checks.py" },
          "src/viz/__init__.py":            { url: "./src/viz/__init__.py" },
          "src/viz/charts.py":              { url: "./src/viz/charts.py" },
          "src/viz/maps.py":                { url: "./src/viz/maps.py" },
          "data/berne_warnregionen.geojson":
            { url: "./data/berne_warnregionen.geojson" },
          "data/trockenheitsdaten-numerisch_current__trockenheitsdaten-numerisch_current.csv.zip":
            { url: "./data/trockenheitsdaten-numerisch_current__trockenheitsdaten-numerisch_current.csv.zip" },
          "data/trockenheitsdaten-numerisch_historic__trockenheitsdaten-numerisch_historic.csv.zip":
            { url: "./data/trockenheitsdaten-numerisch_historic__trockenheitsdaten-numerisch_historic.csv.zip" },
          "data/trockenheitsdaten-numerisch_reference__trockenheitsdaten-numerisch_reference.csv.zip":
            { url: "./data/trockenheitsdaten-numerisch_reference__trockenheitsdaten-numerisch_reference.csv.zip" },
        },
      },
      document.getElementById("root")
    );
  </script>
</body>
</html>
```

- [ ] **Step 3: Commit**

```bash
git add docs/index.html
git commit -m "feat: add stlite index.html mount page for GitHub Pages"
```

---

## Task 5: Create `.github/workflows/deploy.yml` — GitHub Actions CI

**Files:**
- Create: `.github/workflows/deploy.yml`

- [ ] **Step 1: Create the workflow directory and file**

```bash
mkdir -p .github/workflows
```

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to GitHub Pages

on:
  push:
    branches: [main]

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/checkout@v4

      - name: Assemble static site
        run: |
          mkdir -p _site
          cp docs/index.html _site/
          cp app.py _site/
          cp -r config _site/config
          cp -r src _site/src
          cp -r data _site/data

      - name: Upload Pages artifact
        uses: actions/upload-pages-artifact@v3
        with:
          path: _site/

      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v4
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/deploy.yml
git commit -m "ci: add GitHub Actions workflow to deploy stlite app to GitHub Pages"
```

---

## Task 6: Enable GitHub Pages in repository settings (manual)

This task is performed by a human in the GitHub web UI — it cannot be automated.

- [ ] **Step 1: Open repo settings**

Go to the GitHub repository → **Settings** → **Pages** (left sidebar).

- [ ] **Step 2: Set source to GitHub Actions**

Under **Build and deployment → Source**, select **"GitHub Actions"** (not "Deploy from a branch").

Click **Save**.

- [ ] **Step 3: Trigger the first deployment**

Push any commit to `main` (or re-run the workflow manually under **Actions → Deploy to GitHub Pages → Run workflow**).

- [ ] **Step 4: Verify the deployment**

Wait for the workflow to complete (green tick in the **Actions** tab). The Pages URL is printed at the end of the `deploy` job as the `url` output.

Open the URL in a browser and verify:
- The stlite loading screen appears (Pyodide bootstraps in ~5–15 seconds on first load)
- The app renders with the sidebar, CDI map, timeseries chart, and text sections
- Switching region and mode updates the content
- The "HTML exportieren" button downloads a self-contained HTML file
- The `st.info` print note is visible in the sidebar

---

## Self-Review Notes

- **Spec coverage:** All four spec sections covered — app changes (Tasks 1–2), deps (Task 3), static site structure (Task 4), GitHub Actions (Task 5–6). ✓
- **No placeholders:** All code blocks are complete and runnable. ✓
- **Type consistency:** `to_html(doc, report, chart_fig=fig, map_png=map_png)` signature unchanged across Task 1 and Task 2. ✓
- **Risk acknowledged:** `build_export_map()` wrapped in `try/except` in Task 2 to handle any geopandas/Pyodide incompatibility gracefully. ✓
