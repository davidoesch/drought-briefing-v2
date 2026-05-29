# Ruleset integration & canton restructure — design

**Date:** 2026-05-28
**Status:** Draft — pending user review (rebased onto updated `main` after the FR-language work merged)
**Scope:** Single implementation plan (one feature branch)

## Context

The repository has two parallel paths for producing the drought briefing:

1. **Production codepath** (on `main`) — Streamlit app, per-warning-region, two tonal modes (`behoerden` / `bulletin`), text blocks hard-coded in `src/briefing/text_blocks_de.py` plus a French sibling `text_blocks_fr.py` (added by the parallel FR-language workstream — see [Relation to other work](#relation-to-other-work)). Trend computed as current vs. prior week. Bern-only. STAC client is live (fetches from `data.geo.admin.ch` with transparent fixture fallback). A `src/i18n/strings.py` module exposes a `t(key, lang)` function for UI chrome strings (sidebar labels, buttons, metric titles).
2. **Ruleset YAML** (`data/ruleset/example-report.yaml`, merged in PR #1) — declarative, BAFU/MeteoSchweiz terminology, single narrative style, trend computed as forecast vs. current, live BAFU Warnkarte API as the source of truth for the warning level.

The YAML was developed standalone. It is not wired into the app. Today the production code hard-codes content that the YAML now declares (terminology, recommendations, trend phrasing). Two parallel implementations is the worst possible state.

A separately-tracked TODO calls for restructuring the report to be **per canton** instead of per warning region: aggregated lead + two maps (current CDI / forecast CDI week 2), action recommendations for the max warning level across the canton's warning regions, and a new "Allgemeine Lage nach Regionen" section at the bottom containing the existing per-region narrative.

This spec covers both: integrating the YAML *and* restructuring to per-canton in one implementation pass.

## Goals

1. **Single source of truth** for report content: the YAML ruleset.
2. **Per-canton report scope** with aggregated lead, two maps, max-warnlevel-based recommendations, and a per-region breakdown section.
3. **Live BAFU Warnkarte API** as authoritative source for the warning level, with offline fixture fallback.
4. **Bern as launch canton**, architecture canton-agnostic so further cantons can be added without code changes (only data: canton→regions mapping).
5. **Single narrative style** (bulletin / BAFU-MeteoSchweiz terminology). The `behoerden` mode is removed.

## Decisions

These were taken during brainstorming and are foundational to the design:

| # | Decision | Rationale |
|---|---|---|
| 1 | Integration *and* canton restructure in one pass | YAML and existing code conflict structurally; refactoring twice (per-region first, then canton) is wasted effort. |
| 2 | Only bulletin mode is kept | YAML is single-style by design; behoerden mode is a key-value telegram, not a narrative — better served by a future data sheet. |
| 3 | Bern launches, architecture canton-agnostic | Data dependency (canton→regions mapping) only exists for Bern; full Swiss coverage is a separate data-gathering effort. |
| 4 | Live API with cache and fixture fallback | Production-grade resilience without making the app fragile against network outages. |
| 5 | Big-bang refactor (no feature flag) | Architectural conflicts are too fundamental for graceful coexistence; feature flags would invite indefinite legacy maintenance. |

## Architecture overview

New pipeline shape (preserves the existing pipeline-first principle):

```
DataBundle ──┐
             ├─► CantonReport ──► BriefingDocument ──► UI / Export
WarnkarteData ┘     │
                    └── contains N RegionReports + canton aggregates
                        (max_warnlevel, region counts by index level, etc.)
```

### Status of existing components

| Existing | Status | Replacement / change |
|---|---|---|
| `DataBundle` | unchanged | — |
| `RegionReport` | retained, extended | New fields for the per-region section: `precip_sum_1m`, `precip_sum_3m`, `precip_1m_index`, `soil_moisture_index`, `warnlevel`, `warnlevel_info_de`, `cdi_forecast_week2` |
| `BriefingDocument` | retained, extended | `sections: dict[str, str]` keys become `lead`, `allgemeine_lage`, `handlungsoptionen`, `regionen`, `datenquellen` (Markdown). New attribute `lead_maps: list[MapSpec]` holds the structured map specs from the YAML lead block — kept separate from `sections` so the Markdown dict stays a flat string-to-string mapping. |
| `src/data/stac_client.py` | unchanged | Already does live STAC fetch with transparent fixture fallback. The `warnkarte_client` adopts the same `try fetch / except: fixture` pattern. |
| `src/i18n/strings.py` | unchanged | UI chrome strings (sidebar, buttons, metric titles, quality panel) stay here. YAML handles report content; i18n stays the source for everything not in the report body. |
| `text_blocks_de.py` + `text_blocks_fr.py` | **both deleted** | Report content (DE and FR) moves into the YAML ruleset (`nomenclature` + `sections.template`). FR content is currently stub-y in the YAML and gets filled out as part of step 4. |
| `template.py::build_briefing(report, mode, lang)` | **rewritten** | New `render_briefing(canton_report, ruleset, locale)`. `lang` becomes `locale` to align with the YAML's de/fr/it scheme. |
| `_TREND_LABELS` (in `template.py`) | **deleted** | Trend term comes from `trend.defizit` in the YAML |
| Sidebar mode radio | **removed** | Single narrative style |
| Sidebar region selector | becomes **canton selector** | Bern initially, canton-agnostic |
| Sidebar language toggle | unchanged | Stays as is. `t()` is used for chrome; `render_briefing(..., locale=lang)` flows the selected language into the YAML render. |

### New components

- `src/data/warnkarte_client.py` — HTTP adapter for the BAFU Warnkarte. `@st.cache_data(ttl=3600)` on the fetch function. On error, loads `data/warnkarte_fixture.json` (the last successful response with timestamp).
- `src/aggregation/canton.py` — `compute_canton_report(canton_id, bundle, warnkarte_data) -> CantonReport`.
- `src/briefing/renderer.py` — YAML loader + Jinja2 environment with custom filters (`format_date`) and globals (`trend`, `nomenclature`). Exposes `load_ruleset(path)` and `render_briefing(canton_report, ruleset, locale="de")`.
- `src/briefing/schemas.py` — Pydantic models validating the YAML shape (`extra="forbid"`, `StrictUndefined`-friendly).
- `src/models.py` — extended with `CantonReport`, `WarnkarteEntry`, `MapSpec`.

### Engine choice: Jinja2

The YAML was authored in Handlebars-style syntax (`{{#each X}} … {{/each}}`, `{{ this.field }}`). Jinja2 is the de-facto Python templating engine, supports the same primitives (`{% for item in X %} … {% endfor %}`), and exposes custom filters/globals cleanly. A 15-line preprocessor in `load_ruleset()` rewrites the Handlebars constructs to Jinja2 before compiling — the YAML stays Handlebars-style for the author.

## YAML schema evolution

The current `data/ruleset/example-report.yaml` is per-region. It is renamed to `data/ruleset/canton-bulletin.yaml` and restructured for canton scope.

### Unchanged blocks

- `data_sources` (warnkarte, trockenheitsdaten_numerisch)
- `references`
- `nomenclature` (cdi, niederschlag, hydro, bodenfeuchte)
- `trend.defizit`
- `handlungsempfehlungen` (levels 1–5 with fallback)

### Changed: `lead.warnstufe`

- Headline template references `canton.max_warnlevel` and `canton.max_warnlevel_info_de` (was `warnkarte.warnlevel` per region).
- New sub-block `maps:` declares the two maps rendered next to the lead:

  ```yaml
  lead:
    warnstufe:
      headline: …
      meta: …
      farben_pro_stufe: …
      maps:
        - id: cdi_current
          title: { de: "Aktueller CDI" }
          source: canton.regions[*].cdi
          style: choropleth_warnregionen
        - id: cdi_forecast_week2
          title: { de: "CDI-Prognose Woche 2" }
          source: canton.regions[*].cdi_forecast_week2
          style: choropleth_warnregionen
  ```

  Maps are declarative specs in the YAML. The renderer materialises them as `MapSpec` objects; Streamlit and the HTML exporter render them.

### Changed: `sections`

| ID | Content | Data source |
|---|---|---|
| `allgemeine-lage` | Canton-level aggregate narrative ("Im Kanton Bern weisen 4 von 6 Warnregionen ein leichtes Niederschlagsdefizit auf …") | `canton.*` aggregates |
| `handlungsoptionen` | Bullet list based on `canton.max_warnlevel` | `handlungsempfehlungen.by_gefahrenstufe[canton.max_warnlevel]` |
| `regionen` (new) | Iterates over `canton.regions` and renders the existing per-region "Allgemeine Lage" text as a sub-section | per region: `region.*`, `weekly_current_regions.*`, `weekly_forecast_regions.*` |
| `datenquellen` | Auto-generated from `data_sources` + `references` (unchanged) | the YAML itself |

### New: top-level `context` block

```yaml
context:
  scope: canton                   # was implicitly per region
  required_inputs:
    canton_id: "BFS canton ID (e.g. 2 for Bern)"
```

## Data flow

```
1. User selects canton_id = 2 (Bern) in the sidebar
   ↓
2. CANTON_TO_REGIONS[2] = {33, 34, 35, 37, 38, 41}
   ↓
3. bundle = load_data()                                # existing, cached @1h
   ↓
4. warnkarte_data = warnkarte_client.fetch_for_regions([33,34,...])
   ↑ HTTP per region, @st.cache_data(ttl=3600), fallback to data/warnkarte_fixture.json
   ↓
5. region_reports = [compute_region_report(rid, bundle, warnkarte_data[rid])
                     for rid in CANTON_TO_REGIONS[2]]
   ↑ RegionReport gains: warnlevel, warnlevel_info_de, precip_sum_1m,
     precip_sum_3m, precip_1m_index, soil_moisture_index, cdi_forecast_week2
   ↓
6. canton_report = compute_canton_report(canton_id=2, region_reports)
   ↑ CantonReport contains:
     - canton_name_de, regions, max_warnlevel, max_warnlevel_info_de
     - n_regions_by_precip_index, n_regions_by_soil_moisture_index, n_regions_by_hydro_index
     - data_timestamp, source, quality (aggregated)
   ↓
7. ruleset = load_ruleset("data/ruleset/canton-bulletin.yaml")  # session-cached
   ↓
8. doc = render_briefing(canton_report, ruleset, locale="de")
   ↑ Jinja2 env with:
       env.filters["format_date"] = format_date
       env.globals["trend"] = trend_for_indicator
       env.globals["nomenclature"] = ruleset.nomenclature
     Sections rendered in declared YAML order. MapSpecs attached to doc.lead_maps.
   ↓
9. app.py renders:
     - lead box + two maps (build_canton_map(canton_report, map_spec) for map_spec in doc.lead_maps)
     - doc.sections["allgemeine_lage"] (Markdown)
     - doc.sections["handlungsoptionen"] (Markdown bullets)
     - doc.sections["regionen"] (per-region sub-sections)
     - doc.sections["datenquellen"]
     - quality expander (canton-aggregated)
     - export button → to_html(doc, canton_report)
```

### Cache strategy

| Layer | TTL | Notes |
|---|---|---|
| `load_data()` | 1 h | unchanged |
| `warnkarte_client.fetch_for_regions()` | 1 h | small payload, network call |
| `load_ruleset()` | session | YAML changes only on deploy |

## Error handling

### Recoverable degradation (report renders, user is informed)

| Scenario | Behaviour |
|---|---|
| BAFU Warnkarte unreachable / 5xx / timeout | `WarnkarteClient` loads `data/warnkarte_fixture.json`. UI shows a 🟡 banner: "Warnstufen offline geladen, letzter Stand: DD.MM.YYYY". |
| Forecast week 2 not in the dataset | `cdi_forecast_week2 = None` for affected regions. Map shows them in grey with a tooltip; the `allgemeine-lage` wording omits the forecast sentence conditionally. |
| A region has no current CSV row | Region marked `has_data = False`. Skipped in the `regionen` section with a short "Keine Daten verfügbar". Canton aggregates ignore the region. |
| VHI = NaN (legitimate, e.g. region 37) | Display "–" instead of a number. Aggregates ignore NaN. |

### Fail fast (report does not render)

| Scenario | Behaviour |
|---|---|
| `DataBundle` cannot load | `st.error("Datengrundlage nicht verfügbar: …")`. No sections rendered. |
| Canton ID not in `CANTON_TO_REGIONS` | `st.error("Kanton X nicht unterstützt. Aktuell verfügbar: Bern.")`. |
| YAML parse error or schema mismatch | `st.error("Ruleset konnte nicht geladen werden: …")`. Pydantic-validated at load time. |
| Jinja2 `UndefinedError` | App crashes loudly with stack trace — this is a developer bug, not a runtime edge case. |

### Canton-level quality aggregation

`CantonReport.quality` is folded from per-region `QualityReport`s:

- `data_age_days = max` across regions
- `coverage_pct = mean` coverage
- `overall = worst` (any "error" → canton "error")
- `outlier_flags = union` with region prefix ("R34: SPI-3m outlier")

Surfaced in the existing quality expander, with a per-region drill-down.

### Explicitly not in scope

- No retries on API failure — the fixture fallback is faster than three timeouts.
- No partial rendering on `DataBundle` failure — confuses more than it helps.
- No external telemetry — the Streamlit logger is sufficient.

## Ruleset loader and renderer

### Module shape

```python
# src/briefing/renderer.py

class RulesetSchema(BaseModel):
    id: str
    title: str
    context: ContextSpec
    data_sources: dict[str, DataSourceSpec]
    references: dict[str, ReferenceSpec]
    nomenclature: NomenclatureSpec
    trend: dict[str, TrendSpec]
    handlungsempfehlungen: HandlungsempfehlungenSpec
    lead: LeadSpec
    sections: list[SectionSpec]
    model_config = ConfigDict(extra="forbid")

def load_ruleset(path: Path) -> RulesetSchema:
    """Load YAML, validate via Pydantic, return schema object."""

def render_briefing(
    canton_report: CantonReport,
    ruleset: RulesetSchema,
    locale: Literal["de", "fr", "it"] = "de",
) -> BriefingDocument:
    """Set up Jinja2 environment, render sections in YAML order."""
```

### Jinja2 setup (once per render)

```python
env = Environment(
    loader=BaseLoader(),          # templates come from YAML strings, not disk
    undefined=StrictUndefined,    # missing keys → loud errors
    autoescape=False,             # output is Markdown, not HTML
)
env.filters["format_date"] = _format_date
env.globals["trend"] = _make_trend_resolver(ruleset.trend, locale)
env.globals["nomenclature"] = ruleset.nomenclature
```

### Handlebars → Jinja2 adapter

The YAML uses Handlebars-style iteration. `load_ruleset()` rewrites two constructs:

- `{{#each X}} … {{/each}}` → `{% for item in X %} … {% endfor %}`
- `{{ this.field }}` → `{{ item.field }}`

A single regex pass, ~15 lines. Function calls (`{{ trend(...) }}`, `{{ format_date(...) }}`) are already valid Jinja2 syntax — no rewriting needed.

### File layout (final)

```
src/
  briefing/
    __init__.py
    renderer.py            ← NEW (replaces template.py)
    schemas.py             ← NEW (Pydantic models)
    text_blocks_de.py      ← DELETED
    text_blocks_fr.py      ← DELETED
  data/
    stac_client.py         (unchanged, live STAC fetch with fixture fallback)
    fixture_loader.py      (unchanged)
    warnkarte_client.py    ← NEW (HTTP + fixture fallback, mirrors stac_client pattern)
  aggregation/
    regional.py            (RegionReport gains new fields)
    canton.py              ← NEW (compute_canton_report)
    indicators.py          (unchanged)
  i18n/
    strings.py             (unchanged, UI chrome strings)
  models.py                (+ CantonReport, WarnkarteEntry, MapSpec)
data/
  ruleset/
    canton-bulletin.yaml   ← renamed from example-report.yaml
  warnkarte_fixture.json   ← NEW (seeded with current live response)
```

### Testing strategy

| Test file | Status | Coverage |
|---|---|---|
| `tests/test_renderer.py` | NEW | Snapshot test of rendered sections for a fixed `CantonReport`; edge cases (missing forecast, max_warnlevel = 1 vs. 4, etc.) |
| `tests/test_warnkarte_client.py` | NEW | Mocked HTTP responses + fixture-fallback path |
| `tests/test_canton.py` | NEW | `compute_canton_report` with region aggregates |
| `tests/test_text_blocks.py` | DELETED | DE module gone |
| `tests/test_briefing_fr.py` | DELETED | FR module gone (FR content moves to YAML) |
| `tests/test_i18n.py` | unchanged | UI chrome strings continue to be tested |
| `tests/test_export.py` | ADAPTED | Now operates on `CantonReport` |
| `tests/test_aggregation.py` | EXTENDED | New `RegionReport` fields |
| `tests/test_quality.py` | EXTENDED | Canton-level quality folding |
| `tests/test_fixture_loader.py` | unchanged | — |

Pydantic schema validation is implicit in `load_ruleset` — no separate schema test required.

## Migration plan

Each step is a commit, lands independently, keeps the UI green except where called out:

1. **Foundation** — add `WarnkarteEntry`, `CantonReport`, `MapSpec` to `src/models.py`; extend `RegionReport`. Dataclass-construction tests.
2. **WarnkarteClient** — `src/data/warnkarte_client.py` + initial `data/warnkarte_fixture.json` (one-shot seeded from the live API). Tests with the `responses` library.
3. **Canton aggregation** — `src/aggregation/canton.py::compute_canton_report()` + extension of `regional.py`. Add to `config/settings.py`:

   ```python
   CANTON_TO_REGIONS: Final[dict[int, frozenset[int]]] = {
       2: frozenset({33, 34, 35, 37, 38, 41}),   # Bern (BFS canton ID 2)
   }
   CANTON_NAMES: Final[dict[int, str]] = {2: "Bern"}
   ```

   `BERNE_REGION_IDS` stays for backwards compatibility until step 9.
4. **YAML restructure** — rename to `data/ruleset/canton-bulletin.yaml`. Lead block switches to `canton.max_warnlevel`, `maps:` sub-block added, `sections` reordered (`allgemeine-lage` as aggregate, `regionen` as iteration). Done first so the schema in step 5 targets the final shape directly.
5. **Ruleset schema + loader** — Pydantic models in `src/briefing/schemas.py`, `load_ruleset()` in `renderer.py`. Validates the canton-bulletin.yaml shape (now on disk from step 4).
6. **Renderer** — `render_briefing()` with Jinja2, Handlebars adapter, custom filters and globals. Snapshot test against a fixed `CantonReport`.
7. **Maps** — `src/viz/maps.py::build_canton_map(canton_report, map_spec: MapSpec)` for both new maps, reusing the existing geopandas/folium code.
8. **`app.py` rewire** — sidebar mode-radio removed, region selector becomes canton selector. Pipeline: `compute_region_report` → `compute_canton_report`. Sections loop uses new keys. Quality panel uses canton aggregation. **This is the cut-over commit — first commit where the user sees the new UI.**
9. **Cleanup** — delete `text_blocks_de.py`, `text_blocks_fr.py`, `template.py`, `tests/test_text_blocks.py`, `tests/test_briefing_fr.py`, `_TREND_LABELS`, `BERNE_REGION_IDS`.

### Validation

- Visual A/B: screenshot of region 34 (old) vs. canton Bern (new). Plausibility-check the `allgemeine-lage` aggregates against the per-region texts.
- `pytest tests/ -v` must pass fully.
- Manual: trigger a BAFU Warnkarte live call (clear cache, fetch region 34), then disable network and verify the fixture fallback.
- Open the exported HTML in a browser and verify CDI maps and texts.

## Out of scope

- Swisseo VHI dataset integration (separate TODO `add-swisseo-vhi-dataset-to-ruleset`).
- FR/IT content fully written out (schema supports it, content follows separately).
- Cantons beyond Bern (architecture is canton-agnostic; data mapping is the blocker).
- Quality-panel UI redesign (only the aggregation is rewired).

## Open questions

These should be answered before implementation starts but are not blocking for the spec sign-off:

1. **"CDI forecast Woche 2" semantics** — does this mean the second week ahead (valid_at = today + 14 d) or the 2nd entry of the forecast time series? The spec assumes the former (today + 14 d).
2. **Canton BFS ID for Bern** — the spec assumes BFS canton ID 2. To be verified against the official Swiss canton coding.
3. **Map projection / styling for `choropleth_warnregionen`** — the existing `build_map` in `src/viz/maps.py` already produces a folium map; reuse and adapt, or build a fresh one. To be decided during step 7.
4. **`warnkarte_fixture.json` refresh policy** — the fixture is seeded once and never updated by the app. Should there be a `scripts/refresh_warnkarte_fixture.py` for periodic regeneration? Probably yes, but not blocking.

## Risks

- **Jinja2 / Handlebars mismatch surprises** — edge cases beyond `{{#each}}` and `{{ this.x }}` may surface. Mitigation: the YAML is small; the snapshot tests catch divergence early.
- **Per-canton max_warnlevel may surprise stakeholders** — a single small region driving a "Stufe 4" headline for the whole canton may be misleading. Mitigation flagged as an open question to validate with the user post-launch; alternative (modal level, area-weighted) is a one-line change in `compute_canton_report`.
- **BAFU Warnkarte API breaking changes** — field renames in `feature.attributes`. Mitigation: Pydantic validates the response shape; failure cleanly degrades to fixture.
- **FR YAML content not yet fleshed out** — the FR translations currently in `text_blocks_fr.py` are richer than what's in the YAML's section templates (only DE templates exist; `nomenclature` is trilingual but `sections.template` is DE-only). Step 4 must port the FR text content into the YAML before step 9 deletes `text_blocks_fr.py`, otherwise FR users lose content. Mitigation: explicit acceptance criterion on step 4.

## Relation to other work

A parallel workstream added French language support to the existing per-region briefing. It is now on `main`:

- Spec: `docs/superpowers/specs/2026-05-28-french-language-design.md`
- Plan: `docs/superpowers/plans/2026-05-28-french-language.md`
- Code: `src/i18n/strings.py`, `src/briefing/text_blocks_fr.py`, FR-aware `template.py`, `src/export/report.py`, `src/viz/charts.py`, sidebar language toggle

**What this spec inherits from that work:**
- Language toggle UX (`de` / `fr`) is established. We keep it.
- `i18n.t(key, lang)` for UI chrome strings is the right abstraction. We keep using it for everything outside the report body.
- Localized chart and HTML export already exist. We do not regress them.

**What this spec changes:**
- The text-block dispatch (`LAGE_BLOCKS_DE` / `LAGE_BLOCKS_FR` keyed by mode and CDI) is replaced by the YAML ruleset. The mode dimension (`behoerden` / `bulletin`) collapses to bulletin only. The language dimension (`de` / `fr`) is preserved via the YAML's `de` / `fr` keys.
- `template.py::build_briefing(report, mode, lang)` becomes `renderer.py::render_briefing(canton_report, ruleset, locale)`. The `mode` parameter goes away.

**Coordination:** step 4 (YAML restructure) must port the existing FR content from `text_blocks_fr.py` into the YAML's section templates before step 9 can delete `text_blocks_fr.py`. This is the only sequencing constraint added by the inheritance.
