# One Click Drought Briefing

**Automated drought situation reports for Swiss authorities — from open federal data to a ready-to-share bulletin in seconds.**

Built at [GovTech Hackathon 2026](https://hack.govtech.ch) in partnership with swisstopo, BAFU (FOEN), and MeteoSwiss.

**[Live Demo (GitHub Pages)](https://cboodnee.github.io/Drought-Briefing/) · [Streamlit Cloud](https://drought-briefing.streamlit.app/)**

---

## The Problem

> Challenge here 👉 https://govtech.digisus-lab.ch/project/16

During drought events, cantonal and municipal crisis teams must quickly assess the situation and communicate it in plain language. Today that means manually pulling data from multiple federal portals, interpreting technical indicators, and writing reports by hand — a process that takes hours, produces inconsistent results across cantons, and only happens at all when a federal warning is already active.

## What We Built

A one-click pipeline that turns federal open data into a structured, bilingual (DE/FR) drought bulletin for any Swiss canton — in seconds. The bulletin includes:

- **Warning level badge** (BAFU Gefahrenstufe 1–5) with plain-language situation summary
- **Regional breakdown** — CDI, SPI-3m, soil moisture, VHI, precipitation, and discharge per Warnregion
- **Interactive map** (choropleth by CDI / warning level) with static PNG fallback for export
- **Time-series chart** (CDI trend + SPI-3m, 52 weeks)
- **Action recommendations** driven by the warning level, populated from a YAML ruleset
- **Expert note fields** per region — editable before export
- **Self-contained HTML export** — no external URLs, suitable for government infrastructure
- **Data quality banner** — staleness, coverage, and outlier flags surfaced automatically

## How It Works

```
DataBundle (STAC / fixtures)
    → CantonReport (aggregation pipeline)
        → BriefingDocument (Jinja2 / YAML ruleset)
            → Streamlit UI  +  HTML export
```

Data is loaded from the [BGDI STAC collection `ch.bafu.trockenheitsdaten-numerisch`](https://www.trockenheit.admin.ch), with live fallback to fixture data. Warning levels are fetched from the geo.admin.ch REST API (`ch.bafu.trockenheitswarnkarte`). Vegetation health (VHI) is fetched from SwissEO. All three clients fall back to bundled fixture data when the network is unavailable.

Bulletin text lives entirely in `data/ruleset/canton-bulletin.yaml` — no strings are hardcoded in Python. Thresholds, action recommendations, nomenclature, and section templates are all editable without touching code.

## Data Sources

| Source | What we use |
|---|---|
| BGDI STAC `ch.bafu.trockenheitsdaten-numerisch` | CDI, SPI, soil moisture, precipitation, hydro indices (weekly per Warnregion) |
| geo.admin.ch REST API `ch.bafu.trockenheitswarnkarte` | Official BAFU warning level (Gefahrenstufe 1–5) per region |
| SwissEO VHI endpoint | Vegetation Health Index per region |
| hydrodaten.admin.ch (BAFU station CSVs) | Discharge (Abfluss) per hydro station with low-flow thresholds |
| `data/kantone_warnregionen.json` | Canton → Warnregion mapping, center coordinates |

## Running Locally

**Docker (recommended):**
```bash
make build
make up        # → http://localhost:8501
```

**Local (requires [uv](https://github.com/astral-sh/uv)):**
```bash
uv run streamlit run app.py
uv run pytest tests/ -v
```

## Team

David Oesch · Joan Sturm · Fabia Huesler · Christopher Boodnee · Lea Stauber · Benjamin Meyer · Luca Huesler · Simon Jaun · Chantal Camenisch
