# stlite / GitHub Pages Deployment

**Date:** 2026-05-28  
**Goal:** Run the Drought Briefing app as a fully static site on GitHub Pages using stlite (Streamlit in WebAssembly via Pyodide). No server required.

---

## 1. App Code Changes

### `app.py`

| Before | After |
|--------|-------|
| `from streamlit_folium import st_folium` | removed |
| `st_folium(folium_map, width=None, height=300, returned_objects=[])` | `st.components.v1.html(folium_map._repr_html_(), height=300)` |
| PDF `st.download_button` + `to_pdf()` call | `st.info("💡 PDF: Datei → Drucken → Als PDF speichern (Ctrl+P)")` |

The HTML export button is kept. `build_export_map()` (matplotlib static PNG) is kept for the HTML export.

### `src/export/report.py`

| Before | After |
|--------|-------|
| `_chart_to_png_b64(fig)` via kaleido → PNG bytes → base64 | `pio.to_html(fig, full_html=False, include_plotlyjs='inline')` → interactive HTML |
| `<img src="data:image/png;base64,...">` in output | `<div>` containing Plotly interactive chart HTML |

`include_plotlyjs='inline'` embeds the plotly.js bundle — no external URLs, satisfies government infra requirements.

The static map path (`build_export_map` → matplotlib → base64 PNG) is unchanged.

---

## 2. Dependency Changes (`pyproject.toml`)

**Remove** (cannot run in WASM):
- `weasyprint` — Cairo-based PDF renderer, no WASM build
- `kaleido` — Chromium binary for Plotly→PNG, no WASM build
- `streamlit-folium` — custom Streamlit component, requires live server
- `pystac-client` — unused (`_fetch_from_stac` always raises `NotImplementedError`)
- `requests` — unused at runtime (same reason)

**Keep** (available in Pyodide):
- `pandas`, `plotly`, `geopandas`, `shapely`, `matplotlib`, `folium`, `pypdf`

**stlite packages** listed in `docs/index.html`:
```
pandas, plotly, geopandas, matplotlib, folium
```
(`shapely` is pulled transitively by `geopandas`.)

**Risk:** `geopandas` in Pyodide uses the `pyogrio` backend — both are in Pyodide's package list and expected to work. If `build_export_map()` fails at runtime, `to_html()` already handles `map_png=None` gracefully (the map image is simply omitted from the HTML export).

---

## 3. Static Site Structure

```
docs/
  index.html          ← stlite mount page (committed to repo)
  app.py              ← assembled by CI
  config/
    __init__.py
    settings.py
  src/
    models.py
    aggregation/…
    briefing/…
    data/…
    export/…
    quality/…
    viz/…
  data/
    berne_warnregionen.geojson
    trockenheitsdaten-numerisch_current__*.csv.zip
    trockenheitsdaten-numerisch_historic__*.csv.zip
    trockenheitsdaten-numerisch_reference__*.csv.zip
```

`docs/index.html` is the only deployable web asset in `docs/` committed to the repo (`docs/superpowers/` holds design docs and is excluded from the CI copy). The rest of the site is assembled by CI each deploy.

### `docs/index.html` structure

```html
<!DOCTYPE html>
<html lang="de">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Trockenheitsbriefing Kanton Bern</title>
  <link rel="stylesheet"
    href="https://cdn.jsdelivr.net/npm/@stlite/mountable@0.73.0/build/stlite.css" />
</head>
<body>
  <div id="root"></div>
  <script src="https://cdn.jsdelivr.net/npm/@stlite/mountable@0.73.0/build/stlite.js"></script>
  <script>
    stlite.mount(
      {
        requirements: ["pandas", "plotly", "geopandas", "matplotlib", "folium"],
        entrypoint: "app.py",
        files: {
          "app.py":                          { url: "./app.py" },
          "config/__init__.py":              { url: "./config/__init__.py" },
          "config/settings.py":              { url: "./config/settings.py" },
          /* … all src/ files … */
          "data/berne_warnregionen.geojson": { url: "./data/berne_warnregionen.geojson" },
          "data/<current>.csv.zip":          { url: "./data/<current>.csv.zip" },
          "data/<historic>.csv.zip":         { url: "./data/<historic>.csv.zip" },
          "data/<reference>.csv.zip":        { url: "./data/<reference>.csv.zip" },
        },
      },
      document.getElementById("root")
    );
  </script>
</body>
</html>
```

stlite downloads each file at startup and places it in Pyodide's virtual filesystem. Existing `Path`-based file I/O in `fixture_loader.py` and `maps.py` works without modification.

---

## 4. GitHub Actions Workflow

**File:** `.github/workflows/deploy.yml`  
**Trigger:** push to `main`  
**GitHub Pages setting:** "Deploy from GitHub Actions" (not from branch/folder — no CI commits to `git log`)

```yaml
name: Deploy to GitHub Pages
on:
  push:
    branches: [main]
permissions:
  contents: read
  pages: write
  id-token: write
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/checkout@v4
      - name: Assemble site
        run: |
          mkdir -p _site
          cp docs/index.html _site/
          cp app.py _site/
          cp -r config _site/config
          cp -r src _site/src
          cp -r data _site/data
      - uses: actions/upload-pages-artifact@v3
        with:
          path: _site/
      - id: deployment
        uses: actions/deploy-pages@v4
```

---

## Out of Scope

- Live STAC data fetch (already raises `NotImplementedError`; fixture data always used)
- Scheduled data refresh (future: add a cron trigger to the workflow once STAC fetch is implemented)
- PDF generation server-side (replaced by browser `Ctrl+P` note)
