# Canton Selection via kantone_warnregionen.json

**Date:** 2026-05-29  
**Status:** Approved

## Goal

Enable the user to select any of the 26 Swiss cantons in the Streamlit UI. Currently only Bern (BFS ID 2) is available because `CANTON_TO_REGIONS` and `CANTON_NAMES` in `config/settings.py` are hardcoded for Bern only. The JSON file `data/kantone_warnregionen.json` contains the full canton→warnregionen mapping and becomes the authoritative source for all non-Bern cantons.

## Approach

Load `kantone_warnregionen.json` at runtime inside `config/settings.py` to build the canton dicts. Bern's 6-region curated mapping is preserved by hardcoding it before the JSON loop runs.

## Changes

### `config/settings.py`

1. **`CANTON_TO_REGIONS`** — Build dynamically:
   - Start with Bern hardcoded: `{2: frozenset({33, 34, 35, 37, 38, 41})}`
   - Read `data/kantone_warnregionen.json` at module load
   - For every canton in the JSON whose `KANTONSNUM` is not 2, add `{KANTONSNUM: frozenset(region["REGION_NR"] for region in canton["warnregionen"])}` 

2. **`CANTON_NAMES`** — Hardcoded dict of all 26 cantons with `de` and `fr` keys. The JSON only provides German names; French names are standard and hardcoded directly.

3. **`CANTON_CENTER_POINTS`** — New constant: parse the `MAPGEO` field (e.g. `&center=2691805,1252035&z=9`) from each JSON entry into `{KANTONSNUM: (x_lv95, y_lv95)}`. Used by `maps.py` to correctly center and zoom the map for any canton.

### `maps.py`

- Replace the hardcoded `CANTON_IDENTIFY_POINTS` dict with an import of `CANTON_CENTER_POINTS` from `config.settings`. The existing `.get(canton_id, CANTON_IDENTIFY_DEFAULT)` fallback in `_fetch_canton_geometry` remains unchanged.
- The hardcoded export map title `"Trockenheitsindex – Kanton Bern"` in `build_export_map` is noted as stale, but `build_export_map` is not called in the current pipeline (`to_html` accepts `map_png=None`; `app.py` passes no PNG). No change required now; fix when the export map is wired up.

### `app.py`

No structural changes. The canton `st.selectbox` already reads from `CANTON_TO_REGIONS.keys()` and `CANTON_NAMES`, so all 26 cantons appear automatically once `settings.py` is updated.

## What does NOT change

- Bern's 6 curated regions (`{33, 34, 35, 37, 38, 41}`) are preserved exactly.
- The `app.py` pipeline, aggregation layer, briefing renderer, and export layer are unchanged.
- The `_load_warnkarte` Streamlit cache key (`region_ids: tuple[int, ...]`) already handles per-canton caching correctly.
- The geo.admin.ch identify endpoint in `_fetch_canton_geometry` already resolves any canton polygon by ID.

## Out of scope

- Filtering cantons by data availability (all 26 are enabled; the CDI fixture covers all Swiss warnregionen 31–68).
- Italian canton names (not used in the current UI).
- Canton-specific GeoJSON fixtures (the live identify endpoint is used for all cantons).
