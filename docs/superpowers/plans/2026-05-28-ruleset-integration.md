# Ruleset Integration & Canton Restructure Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the hard-coded `text_blocks_de.py` + `text_blocks_fr.py` + mode-toggle architecture with a single YAML-driven rule-based renderer, and switch the report scope from per-warning-region to per-canton (lead-block + two CDI maps + max-warnlevel recommendations + per-region breakdown section).

**Architecture:** New `CantonReport` dataclass aggregates N existing `RegionReport`s plus canton-level fields (`max_warnlevel`, region counts by index level). `src/briefing/renderer.py` (Jinja2 + Pydantic-validated YAML) replaces `template.py` + `text_blocks_*.py`. `src/data/warnkarte_client.py` fetches the BAFU Warnkarte API per region with a transparent fixture fallback (same pattern as the existing `stac_client.py`). FR content is ported from `text_blocks_fr.py` into the YAML before the legacy files are deleted.

**Tech Stack:** Python 3.12, Streamlit, Pydantic v2, Jinja2, `requests` (for HTTP), `responses` (for HTTP mocking in tests), pytest.

**Reference:** Design spec at `docs/superpowers/specs/2026-05-28-ruleset-integration-design.md`. Read it before starting.

---

## Phase 0: Setup

### Task 0.1: Add Jinja2, Pydantic, responses dependencies

**Files:**
- Modify: `pyproject.toml`

- [ ] **Step 1: Add runtime deps**

```bash
uv add jinja2 pydantic
```

Expected: `pyproject.toml` updated, `uv.lock` regenerated.

- [ ] **Step 2: Add test dep**

```bash
uv add --dev responses
```

Expected: dev dep added.

- [ ] **Step 3: Verify existing tests still pass**

```bash
uv run pytest tests/ -v
```

Expected: All pre-existing tests pass.

- [ ] **Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "chore: add jinja2, pydantic, and responses dependencies"
```

---

## Phase 1: Foundation Dataclasses (Spec migration step 1)

### Task 1.1: Add `MapSpec` to `src/models.py`

**Files:**
- Modify: `src/models.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Write the failing test**

Create `tests/test_models.py` (if it doesn't exist) and add:

```python
# tests/test_models.py
from src.models import MapSpec


def test_map_spec_construction():
    spec = MapSpec(
        id="cdi_current",
        title_de="Aktueller CDI",
        title_fr="CDI actuel",
        source="canton.regions[*].cdi",
        style="choropleth_warnregionen",
    )
    assert spec.id == "cdi_current"
    assert spec.style == "choropleth_warnregionen"
```

- [ ] **Step 2: Run the test to verify it fails**

```bash
uv run pytest tests/test_models.py::test_map_spec_construction -v
```

Expected: FAIL with `ImportError: cannot import name 'MapSpec'`.

- [ ] **Step 3: Add the dataclass**

In `src/models.py`, append:

```python
@dataclass
class MapSpec:
    id: str
    title_de: str
    title_fr: str
    source: str            # path expression into CantonReport, e.g. "canton.regions[*].cdi"
    style: str             # renderer hint, e.g. "choropleth_warnregionen"
```

- [ ] **Step 4: Run to verify it passes**

```bash
uv run pytest tests/test_models.py::test_map_spec_construction -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/models.py tests/test_models.py
git commit -m "feat(models): add MapSpec dataclass for declarative map specs"
```

### Task 1.2: Add `WarnkarteEntry` to `src/models.py`

**Files:**
- Modify: `src/models.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_models.py`:

```python
from datetime import datetime

from src.models import WarnkarteEntry


def test_warnkarte_entry_construction():
    entry = WarnkarteEntry(
        drought_region_id=34,
        warnlevel=2,
        info_de="Mässige Gefahr",
        info_fr="Danger limité",
        info_it="Pericolo moderato",
        valid_from=datetime(2026, 5, 28),
    )
    assert entry.warnlevel == 2
    assert entry.info_de == "Mässige Gefahr"
```

- [ ] **Step 2: Run to verify it fails**

```bash
uv run pytest tests/test_models.py::test_warnkarte_entry_construction -v
```

Expected: FAIL with `ImportError`.

- [ ] **Step 3: Add the dataclass**

In `src/models.py`:

```python
@dataclass
class WarnkarteEntry:
    drought_region_id: int
    warnlevel: int          # 1-5 (BAFU Gefahrenstufe)
    info_de: str
    info_fr: str
    info_it: str
    valid_from: datetime
```

- [ ] **Step 4: Run to verify it passes**

```bash
uv run pytest tests/test_models.py -v
```

Expected: Both model tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/models.py tests/test_models.py
git commit -m "feat(models): add WarnkarteEntry dataclass for BAFU warning API"
```

### Task 1.3: Add `CantonReport` to `src/models.py`

**Files:**
- Modify: `src/models.py`
- Test: `tests/test_models.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_models.py`:

```python
from src.models import CantonReport, QualityReport, RegionReport


def _make_minimal_region_report(rid: int, cdi: int = 2) -> RegionReport:
    return RegionReport(
        region_id=rid,
        region_name_de=f"Region {rid}",
        data_timestamp=datetime(2026, 5, 18),
        source="fixture",
        cdi=cdi,
        spi_3m=-0.5,
        soil_moisture_pct=60.0,
        vhi=50.0,
        cdi_trend=0,
        spi_3m_delta=0.0,
        vhi_delta=0.0,
        pct_critical=0.1,
        spi_3m_percentile=40,
        quality=QualityReport(
            data_age_days=3,
            coverage_pct=1.0,
            missing_columns=[],
            outlier_flags=[],
            is_stale=False,
            overall="ok",
        ),
    )


def test_canton_report_construction():
    regions = [_make_minimal_region_report(34, cdi=2), _make_minimal_region_report(35, cdi=4)]
    canton = CantonReport(
        canton_id=2,
        canton_name_de="Bern",
        canton_name_fr="Berne",
        data_timestamp=datetime(2026, 5, 18),
        source="fixture",
        regions=regions,
        max_warnlevel=4,
        max_warnlevel_info_de="Grosse Gefahr",
        max_warnlevel_info_fr="Danger élevé",
        n_regions_by_precip_index={1: 1, 2: 1},
        n_regions_by_soil_moisture_index={1: 2},
        n_regions_by_hydro_index={1: 1, 2: 1},
        quality=QualityReport(
            data_age_days=3,
            coverage_pct=1.0,
            missing_columns=[],
            outlier_flags=[],
            is_stale=False,
            overall="ok",
        ),
    )
    assert canton.max_warnlevel == 4
    assert len(canton.regions) == 2
```

- [ ] **Step 2: Run to verify it fails**

```bash
uv run pytest tests/test_models.py::test_canton_report_construction -v
```

Expected: FAIL.

- [ ] **Step 3: Add the dataclass**

In `src/models.py`:

```python
@dataclass
class CantonReport:
    canton_id: int
    canton_name_de: str
    canton_name_fr: str
    data_timestamp: datetime
    source: Literal["api", "fixture"]
    regions: list[RegionReport]
    max_warnlevel: int                                  # 1-5
    max_warnlevel_info_de: str
    max_warnlevel_info_fr: str
    n_regions_by_precip_index: dict[int, int]           # e.g. {1: 4, 2: 2}
    n_regions_by_soil_moisture_index: dict[int, int]
    n_regions_by_hydro_index: dict[int, int]
    quality: QualityReport
```

- [ ] **Step 4: Run to verify**

```bash
uv run pytest tests/test_models.py -v
```

Expected: All three model tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/models.py tests/test_models.py
git commit -m "feat(models): add CantonReport dataclass aggregating regions per canton"
```

### Task 1.4: Extend `RegionReport` with new fields

**Files:**
- Modify: `src/models.py`
- Modify: `tests/test_aggregation.py`

- [ ] **Step 1: Add new fields with defaults to keep backwards compatibility**

In `src/models.py`, modify `RegionReport`:

```python
@dataclass
class RegionReport:
    region_id: int
    region_name_de: str
    data_timestamp: datetime
    source: Literal["api", "fixture"]
    cdi: int
    spi_3m: float
    soil_moisture_pct: float
    vhi: float
    cdi_trend: int
    spi_3m_delta: float
    vhi_delta: float
    pct_critical: float
    spi_3m_percentile: int
    quality: QualityReport
    # New fields added 2026-05-28 (defaults preserve backward compat until step 3)
    precip_sum_1m: float = 0.0
    precip_sum_3m: float = 0.0
    precip_1m_index: int = 1
    soil_moisture_index: int = 1
    hydro_index: int = 1
    warnlevel: int = 1
    warnlevel_info_de: str = ""
    warnlevel_info_fr: str = ""
    cdi_forecast_week2: int | None = None
```

- [ ] **Step 2: Run the existing aggregation tests — they should still pass**

```bash
uv run pytest tests/test_aggregation.py -v
```

Expected: PASS (defaults shield the existing call sites).

- [ ] **Step 3: Commit**

```bash
git add src/models.py
git commit -m "feat(models): extend RegionReport with new fields for canton report"
```

---

## Phase 2: WarnkarteClient (Spec migration step 2)

### Task 2.1: Sketch the WarnkarteClient API surface

**Files:**
- Create: `src/data/warnkarte_client.py`
- Create: `tests/test_warnkarte_client.py`

- [ ] **Step 1: Write the API-shape test (will fail because module doesn't exist)**

```python
# tests/test_warnkarte_client.py
from datetime import datetime
from src.data.warnkarte_client import fetch_for_regions, _parse_response
from src.models import WarnkarteEntry


def test_parse_response_extracts_attributes():
    sample = {
        "feature": {
            "attributes": {
                "idn": 34,
                "warnlevel": 2,
                "info_de": "Mässige Gefahr",
                "info_fr": "Danger limité",
                "info_it": "Pericolo moderato",
                "valid_from": "2026/05/28 00:00:00+00",
            }
        }
    }
    entry = _parse_response(sample)
    assert entry == WarnkarteEntry(
        drought_region_id=34,
        warnlevel=2,
        info_de="Mässige Gefahr",
        info_fr="Danger limité",
        info_it="Pericolo moderato",
        valid_from=datetime(2026, 5, 28),
    )
```

- [ ] **Step 2: Run to verify it fails**

```bash
uv run pytest tests/test_warnkarte_client.py::test_parse_response_extracts_attributes -v
```

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Create the module with parser**

```python
# src/data/warnkarte_client.py
"""
Fetches the current BAFU drought warning level per region.

API endpoint:
  https://api3.geo.admin.ch/rest/services/api/MapServer/ch.bafu.trockenheitswarnkarte/{drought_region_id}

On any network or HTTP error, falls back to the bundled fixture (data/warnkarte_fixture.json).
Same pattern as src/data/stac_client.py.
"""
from __future__ import annotations

import json
import logging
import warnings
from datetime import datetime
from pathlib import Path

from src.models import WarnkarteEntry

logger = logging.getLogger(__name__)

_BASE_URL = "https://api3.geo.admin.ch/rest/services/api/MapServer/ch.bafu.trockenheitswarnkarte"
_TIMEOUT_SECONDS = 10
_FIXTURE_PATH = Path(__file__).resolve().parents[2] / "data" / "warnkarte_fixture.json"


def _parse_response(payload: dict) -> WarnkarteEntry:
    """Convert the API JSON shape into a WarnkarteEntry."""
    attrs = payload["feature"]["attributes"]
    return WarnkarteEntry(
        drought_region_id=int(attrs["idn"]),
        warnlevel=int(attrs["warnlevel"]),
        info_de=str(attrs["info_de"]),
        info_fr=str(attrs["info_fr"]),
        info_it=str(attrs["info_it"]),
        valid_from=datetime.strptime(
            str(attrs["valid_from"]).split("+")[0].strip(),
            "%Y/%m/%d %H:%M:%S",
        ),
    )


def fetch_for_regions(region_ids: list[int]) -> dict[int, WarnkarteEntry]:
    """
    Fetch the current warning level for each region.

    Returns a dict keyed by drought_region_id.
    On any network or HTTP error, falls back to the fixture file.
    """
    try:
        return _fetch_live(region_ids)
    except Exception as exc:
        warnings.warn(
            f"Warnkarte fetch failed ({exc!r}); using bundled fixture data.",
            stacklevel=2,
        )
        return _load_from_fixture(region_ids)


def _fetch_live(region_ids: list[int]) -> dict[int, WarnkarteEntry]:
    import requests

    out: dict[int, WarnkarteEntry] = {}
    for rid in region_ids:
        url = f"{_BASE_URL}/{rid}"
        response = requests.get(url, timeout=_TIMEOUT_SECONDS)
        response.raise_for_status()
        out[rid] = _parse_response(response.json())
    return out


def _load_from_fixture(region_ids: list[int]) -> dict[int, WarnkarteEntry]:
    with _FIXTURE_PATH.open() as f:
        raw = json.load(f)

    out: dict[int, WarnkarteEntry] = {}
    for rid in region_ids:
        key = str(rid)
        if key not in raw:
            raise ValueError(
                f"Region {rid} not present in fixture {_FIXTURE_PATH} — "
                f"available keys: {sorted(raw.keys())}"
            )
        entry = raw[key]
        out[rid] = WarnkarteEntry(
            drought_region_id=int(entry["drought_region_id"]),
            warnlevel=int(entry["warnlevel"]),
            info_de=entry["info_de"],
            info_fr=entry["info_fr"],
            info_it=entry["info_it"],
            valid_from=datetime.fromisoformat(entry["valid_from"]),
        )
    return out
```

- [ ] **Step 4: Run the parse test**

```bash
uv run pytest tests/test_warnkarte_client.py::test_parse_response_extracts_attributes -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/data/warnkarte_client.py tests/test_warnkarte_client.py
git commit -m "feat(data): add warnkarte_client with response parser"
```

### Task 2.2: Add live-fetch test with mocked HTTP

**Files:**
- Modify: `tests/test_warnkarte_client.py`

- [ ] **Step 1: Write the test**

Append to `tests/test_warnkarte_client.py`:

```python
import responses
from src.data.warnkarte_client import fetch_for_regions


@responses.activate
def test_fetch_for_regions_live_path():
    base = "https://api3.geo.admin.ch/rest/services/api/MapServer/ch.bafu.trockenheitswarnkarte"
    responses.add(
        responses.GET,
        f"{base}/34",
        json={
            "feature": {
                "attributes": {
                    "idn": 34,
                    "warnlevel": 2,
                    "info_de": "Mässige Gefahr",
                    "info_fr": "Danger limité",
                    "info_it": "Pericolo moderato",
                    "valid_from": "2026/05/28 00:00:00+00",
                }
            }
        },
        status=200,
    )

    out = fetch_for_regions([34])
    assert 34 in out
    assert out[34].warnlevel == 2
    assert out[34].info_fr == "Danger limité"
```

- [ ] **Step 2: Run to verify it passes**

```bash
uv run pytest tests/test_warnkarte_client.py::test_fetch_for_regions_live_path -v
```

Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/test_warnkarte_client.py
git commit -m "test(warnkarte_client): cover live-fetch path with mocked HTTP"
```

### Task 2.3: Seed the fixture file from live API

**Files:**
- Create: `data/warnkarte_fixture.json`
- Create: `scripts/refresh_warnkarte_fixture.py`

- [ ] **Step 1: Write the refresh script**

```python
# scripts/refresh_warnkarte_fixture.py
"""
Refresh data/warnkarte_fixture.json from the live BAFU Warnkarte API.

Usage:
    uv run python scripts/refresh_warnkarte_fixture.py
"""
import json
from datetime import datetime
from pathlib import Path

import requests

from config.settings import BERNE_REGION_IDS

URL = "https://api3.geo.admin.ch/rest/services/api/MapServer/ch.bafu.trockenheitswarnkarte/{rid}"
FIXTURE = Path(__file__).resolve().parents[1] / "data" / "warnkarte_fixture.json"


def main() -> None:
    out: dict[str, dict] = {}
    for rid in sorted(BERNE_REGION_IDS):
        resp = requests.get(URL.format(rid=rid), timeout=10)
        resp.raise_for_status()
        attrs = resp.json()["feature"]["attributes"]
        valid_from = datetime.strptime(
            str(attrs["valid_from"]).split("+")[0].strip(),
            "%Y/%m/%d %H:%M:%S",
        )
        out[str(rid)] = {
            "drought_region_id": int(attrs["idn"]),
            "warnlevel": int(attrs["warnlevel"]),
            "info_de": attrs["info_de"],
            "info_fr": attrs["info_fr"],
            "info_it": attrs["info_it"],
            "valid_from": valid_from.isoformat(),
        }
    FIXTURE.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"Wrote {len(out)} regions to {FIXTURE}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the script**

```bash
uv run python scripts/refresh_warnkarte_fixture.py
```

Expected: Output `Wrote 6 regions to <path>` and `data/warnkarte_fixture.json` exists.

- [ ] **Step 3: Verify the file**

```bash
cat data/warnkarte_fixture.json | python -m json.tool | head -20
```

Expected: JSON with 6 region entries, each containing warnlevel/info_de/info_fr/info_it/valid_from.

- [ ] **Step 4: Commit**

```bash
git add data/warnkarte_fixture.json scripts/refresh_warnkarte_fixture.py
git commit -m "feat(data): seed warnkarte_fixture.json from BAFU API + refresh script"
```

### Task 2.4: Add fallback test (live fetch fails → fixture loaded)

**Files:**
- Modify: `tests/test_warnkarte_client.py`

- [ ] **Step 1: Write the test**

Append:

```python
@responses.activate
def test_fetch_for_regions_falls_back_to_fixture(recwarn):
    base = "https://api3.geo.admin.ch/rest/services/api/MapServer/ch.bafu.trockenheitswarnkarte"
    responses.add(responses.GET, f"{base}/34", status=503)

    out = fetch_for_regions([34])

    # Fixture must contain region 34
    assert 34 in out
    # The function should have emitted a warning about the fallback
    assert any("fetch failed" in str(w.message) for w in recwarn.list)
```

- [ ] **Step 2: Run**

```bash
uv run pytest tests/test_warnkarte_client.py::test_fetch_for_regions_falls_back_to_fixture -v
```

Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/test_warnkarte_client.py
git commit -m "test(warnkarte_client): verify fixture fallback on HTTP error"
```

---

## Phase 3: Canton Aggregation (Spec migration step 3)

### Task 3.1: Add `CANTON_TO_REGIONS` and `CANTON_NAMES` to settings

**Files:**
- Modify: `config/settings.py`
- Modify: `tests/test_aggregation.py`

- [ ] **Step 1: Add the constants**

In `config/settings.py`, append:

```python
# Canton → drought region mapping.
# Bern is the launch canton. Other cantons will be added when their
# canton→regions mapping is curated.
CANTON_TO_REGIONS: Final[dict[int, frozenset[int]]] = {
    2: frozenset({33, 34, 35, 37, 38, 41}),   # Bern (BFS canton ID 2)
}

CANTON_NAMES: Final[dict[int, dict[str, str]]] = {
    2: {"de": "Bern", "fr": "Berne", "it": "Berna"},
}
```

- [ ] **Step 2: Add a test verifying the lookup**

Append to `tests/test_aggregation.py`:

```python
from config.settings import CANTON_TO_REGIONS, CANTON_NAMES


def test_canton_to_regions_bern():
    assert CANTON_TO_REGIONS[2] == frozenset({33, 34, 35, 37, 38, 41})
    assert CANTON_NAMES[2]["de"] == "Bern"
    assert CANTON_NAMES[2]["fr"] == "Berne"
```

- [ ] **Step 3: Run the test**

```bash
uv run pytest tests/test_aggregation.py::test_canton_to_regions_bern -v
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add config/settings.py tests/test_aggregation.py
git commit -m "feat(config): add CANTON_TO_REGIONS and CANTON_NAMES (Bern launch)"
```

### Task 3.2: Extend `compute_region_report` to populate new fields

**Files:**
- Modify: `src/aggregation/regional.py`
- Modify: `tests/test_aggregation.py`

- [ ] **Step 1: Write the failing test**

Append to `tests/test_aggregation.py`:

```python
from datetime import datetime

from src.aggregation.regional import compute_region_report
from src.data.stac_client import load as load_data
from src.models import WarnkarteEntry


def test_region_report_has_new_fields_from_fixture():
    bundle = load_data()
    warnkarte = {
        34: WarnkarteEntry(
            drought_region_id=34,
            warnlevel=2,
            info_de="Mässige Gefahr",
            info_fr="Danger limité",
            info_it="Pericolo moderato",
            valid_from=datetime(2026, 5, 28),
        )
    }
    report = compute_region_report(34, bundle, warnkarte_entry=warnkarte[34])

    assert report.warnlevel == 2
    assert report.warnlevel_info_de == "Mässige Gefahr"
    assert report.warnlevel_info_fr == "Danger limité"
    assert report.precip_sum_1m >= 0.0
    assert report.precip_sum_3m >= 0.0
    assert 1 <= report.precip_1m_index <= 5
    assert 1 <= report.soil_moisture_index <= 5
    assert 1 <= report.hydro_index <= 5
    # Forecast week 2 may be None if data is shorter than 14 days
    assert report.cdi_forecast_week2 is None or 1 <= report.cdi_forecast_week2 <= 5
```

- [ ] **Step 2: Run, see it fail**

```bash
uv run pytest tests/test_aggregation.py::test_region_report_has_new_fields_from_fixture -v
```

Expected: FAIL — `compute_region_report` doesn't accept `warnkarte_entry`.

- [ ] **Step 3: Read the existing implementation first**

```bash
sed -n '1,100p' src/aggregation/regional.py
```

The existing function body (loading the row, computing prior_cdi, trend, percentile, quality) is kept verbatim. We change two things:

1. Add a parameter `warnkarte_entry: WarnkarteEntry | None = None` to the signature.
2. Add the new field extractions and a helper, then add them to the `return RegionReport(...)` kwargs.

- [ ] **Step 4: Update imports at the top of the file**

Add to the imports block at the top of `src/aggregation/regional.py`:

```python
from datetime import timedelta
from src.models import WarnkarteEntry
```

- [ ] **Step 5: Update the function signature**

Find the line:

```python
def compute_region_report(region_id: int, bundle: DataBundle) -> RegionReport:
```

Replace with:

```python
def compute_region_report(
    region_id: int,
    bundle: DataBundle,
    warnkarte_entry: WarnkarteEntry | None = None,
) -> RegionReport:
```

- [ ] **Step 6: Insert the new field extractions before the `return RegionReport(...)` statement**

Locate the existing `return RegionReport(` line. Immediately before it, insert:

```python
    # --- New fields for canton report (added 2026-05-28) ---
    precip_sum_1m = _safe(row.get("precip_sum_1m"))
    precip_sum_3m = _safe(row.get("precip_sum_3m"))
    precip_1m_index = (
        int(row["precip_1m_index"])
        if not pd.isna(row.get("precip_1m_index"))
        else 1
    )
    soil_moisture_index = (
        int(row["soil_moisture_index"])
        if not pd.isna(row.get("soil_moisture_index"))
        else 1
    )
    hydro_index = (
        int(row["hydro_index"])
        if not pd.isna(row.get("hydro_index"))
        else 1
    )
    cdi_forecast_week2 = _compute_cdi_forecast_week2(bundle, region_id)
    if warnkarte_entry is not None:
        warnlevel = warnkarte_entry.warnlevel
        warnlevel_info_de = warnkarte_entry.info_de
        warnlevel_info_fr = warnkarte_entry.info_fr
    else:
        warnlevel = max(cdi, 1)
        warnlevel_info_de = ""
        warnlevel_info_fr = ""
```

- [ ] **Step 7: Add the new kwargs to the `return RegionReport(...)` call**

Append these keyword arguments to the existing `return RegionReport(...)` call (inside the parentheses, after the existing `quality=quality,` argument):

```python
        precip_sum_1m=precip_sum_1m,
        precip_sum_3m=precip_sum_3m,
        precip_1m_index=precip_1m_index,
        soil_moisture_index=soil_moisture_index,
        hydro_index=hydro_index,
        warnlevel=warnlevel,
        warnlevel_info_de=warnlevel_info_de,
        warnlevel_info_fr=warnlevel_info_fr,
        cdi_forecast_week2=cdi_forecast_week2,
```

- [ ] **Step 8: Add the forecast-week-2 helper at the bottom of the module**

Append to `src/aggregation/regional.py`:

```python
def _compute_cdi_forecast_week2(bundle: DataBundle, region_id: int) -> int | None:
    """Return the CDI forecast for valid_at ≈ today + 14 d. None if forecast horizon is shorter."""
    forecast = getattr(bundle, "forecast_df", None)
    if forecast is None or forecast.empty:
        return None
    target_date = bundle.data_timestamp + timedelta(days=14)
    region_forecast = forecast[forecast["drought_region_id"] == region_id]
    if region_forecast.empty:
        return None
    region_forecast = region_forecast.copy()
    region_forecast["delta"] = (region_forecast["valid_at"] - target_date).abs()
    closest = region_forecast.sort_values("delta").iloc[0]
    if pd.isna(closest.get("cdi_p50")):
        return None
    return int(closest["cdi_p50"])
```

- [ ] **Step 4: Check whether `DataBundle.forecast_df` exists**

```bash
grep -n "forecast" src/models.py src/data/fixture_loader.py
```

If `forecast_df` is not on `DataBundle`, add it now:

In `src/models.py`:

```python
@dataclass
class DataBundle:
    current_df: pd.DataFrame
    historic_df: pd.DataFrame
    reference_df: pd.DataFrame
    forecast_df: pd.DataFrame   # NEW
    data_timestamp: datetime
    source: Literal["api", "fixture"]
```

In `src/data/fixture_loader.py`, load `weekly_forecast_regions.csv` from the current zip and parse it:

```python
# Inside the existing load() function, near where current_df is parsed:
forecast_df = _read_csv_from_zip(
    current_zip, "weekly_forecast_regions.csv", parse_date_col="valid_at"
)
return DataBundle(
    current_df=current_df,
    historic_df=historic_df,
    reference_df=reference_df,
    forecast_df=forecast_df,
    data_timestamp=data_ts,
    source="fixture",
)
```

(`_read_csv_from_zip` is the existing helper — reuse the same signature.)

- [ ] **Step 5: Run the test**

```bash
uv run pytest tests/test_aggregation.py::test_region_report_has_new_fields_from_fixture -v
```

Expected: PASS.

- [ ] **Step 6: Run the full test suite to catch regressions**

```bash
uv run pytest tests/ -v
```

Expected: All pre-existing tests still pass. If any fail because of `forecast_df` being required, add a default value (`field(default_factory=pd.DataFrame)`) and re-run.

- [ ] **Step 7: Commit**

```bash
git add src/models.py src/aggregation/regional.py src/data/fixture_loader.py tests/test_aggregation.py
git commit -m "feat(aggregation): populate new RegionReport fields incl. warnkarte + forecast"
```

### Task 3.3: Create `src/aggregation/canton.py` with the core aggregation

**Files:**
- Create: `src/aggregation/canton.py`
- Create: `tests/test_canton.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_canton.py
from datetime import datetime

from src.aggregation.canton import compute_canton_report
from src.data.stac_client import load as load_data
from src.models import WarnkarteEntry


def _make_warnkarte(rid: int, warnlevel: int) -> WarnkarteEntry:
    info_map = {
        1: ("Keine Gefahr", "Aucun danger"),
        2: ("Mässige Gefahr", "Danger limité"),
        3: ("Erhebliche Gefahr", "Danger marqué"),
        4: ("Grosse Gefahr", "Danger fort"),
        5: ("Sehr grosse Gefahr", "Danger très fort"),
    }
    de, fr = info_map[warnlevel]
    return WarnkarteEntry(
        drought_region_id=rid,
        warnlevel=warnlevel,
        info_de=de,
        info_fr=fr,
        info_it="-",
        valid_from=datetime(2026, 5, 28),
    )


def test_compute_canton_report_basic():
    bundle = load_data()
    warnkarte = {
        33: _make_warnkarte(33, 2),
        34: _make_warnkarte(34, 4),
        35: _make_warnkarte(35, 1),
        37: _make_warnkarte(37, 3),
        38: _make_warnkarte(38, 2),
        41: _make_warnkarte(41, 1),
    }

    canton = compute_canton_report(canton_id=2, bundle=bundle, warnkarte_data=warnkarte)

    assert canton.canton_id == 2
    assert canton.canton_name_de == "Bern"
    assert canton.canton_name_fr == "Berne"
    assert len(canton.regions) == 6
    # Max warnlevel is the highest across regions
    assert canton.max_warnlevel == 4
    assert canton.max_warnlevel_info_de == "Grosse Gefahr"
    # All region IDs appear
    assert {r.region_id for r in canton.regions} == {33, 34, 35, 37, 38, 41}
```

- [ ] **Step 2: Run to verify it fails**

```bash
uv run pytest tests/test_canton.py::test_compute_canton_report_basic -v
```

Expected: FAIL — module missing.

- [ ] **Step 3: Implement `compute_canton_report`**

```python
# src/aggregation/canton.py
from __future__ import annotations

from collections import Counter

from config.settings import CANTON_NAMES, CANTON_TO_REGIONS
from src.aggregation.regional import compute_region_report
from src.models import CantonReport, DataBundle, QualityReport, WarnkarteEntry


def compute_canton_report(
    canton_id: int,
    bundle: DataBundle,
    warnkarte_data: dict[int, WarnkarteEntry],
) -> CantonReport:
    if canton_id not in CANTON_TO_REGIONS:
        raise ValueError(
            f"Canton {canton_id} not in CANTON_TO_REGIONS. "
            f"Available: {sorted(CANTON_TO_REGIONS.keys())}"
        )

    region_ids = sorted(CANTON_TO_REGIONS[canton_id])
    region_reports = [
        compute_region_report(rid, bundle, warnkarte_entry=warnkarte_data.get(rid))
        for rid in region_ids
    ]

    # Max warning level across regions
    max_region = max(region_reports, key=lambda r: r.warnlevel)
    max_warnlevel = max_region.warnlevel
    max_warnlevel_info_de = max_region.warnlevel_info_de
    max_warnlevel_info_fr = max_region.warnlevel_info_fr

    # Index counts
    n_precip = Counter(r.precip_1m_index for r in region_reports)
    n_soil = Counter(r.soil_moisture_index for r in region_reports)
    n_hydro = Counter(r.hydro_index for r in region_reports)

    quality = _fold_quality([r.quality for r in region_reports])

    names = CANTON_NAMES[canton_id]
    return CantonReport(
        canton_id=canton_id,
        canton_name_de=names["de"],
        canton_name_fr=names["fr"],
        data_timestamp=bundle.data_timestamp,
        source=bundle.source,
        regions=region_reports,
        max_warnlevel=max_warnlevel,
        max_warnlevel_info_de=max_warnlevel_info_de,
        max_warnlevel_info_fr=max_warnlevel_info_fr,
        n_regions_by_precip_index=dict(n_precip),
        n_regions_by_soil_moisture_index=dict(n_soil),
        n_regions_by_hydro_index=dict(n_hydro),
        quality=quality,
    )


_QUALITY_RANK = {"ok": 0, "warning": 1, "error": 2}


def _fold_quality(qualities: list[QualityReport]) -> QualityReport:
    """Combine per-region quality reports into one canton-level report."""
    data_age = max(q.data_age_days for q in qualities)
    coverage = sum(q.coverage_pct for q in qualities) / len(qualities)
    missing: list[str] = []
    flags: list[str] = []
    for q in qualities:
        missing.extend(q.missing_columns)
        flags.extend(q.outlier_flags)
    is_stale = any(q.is_stale for q in qualities)
    overall_key = max(_QUALITY_RANK[q.overall] for q in qualities)
    overall = {v: k for k, v in _QUALITY_RANK.items()}[overall_key]
    return QualityReport(
        data_age_days=data_age,
        coverage_pct=coverage,
        missing_columns=sorted(set(missing)),
        outlier_flags=flags,
        is_stale=is_stale,
        overall=overall,
    )
```

- [ ] **Step 4: Run the test**

```bash
uv run pytest tests/test_canton.py -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/aggregation/canton.py tests/test_canton.py
git commit -m "feat(aggregation): add compute_canton_report with max-warnlevel and quality folding"
```

### Task 3.4: Test quality folding edge cases

**Files:**
- Modify: `tests/test_canton.py`

- [ ] **Step 1: Write the test**

```python
from src.aggregation.canton import _fold_quality
from src.models import QualityReport


def _q(overall: str, age: int = 1, coverage: float = 1.0) -> QualityReport:
    return QualityReport(
        data_age_days=age,
        coverage_pct=coverage,
        missing_columns=[],
        outlier_flags=[],
        is_stale=age > 14,
        overall=overall,
    )


def test_fold_quality_worst_wins():
    folded = _fold_quality([_q("ok"), _q("warning"), _q("ok")])
    assert folded.overall == "warning"


def test_fold_quality_error_dominates():
    folded = _fold_quality([_q("ok"), _q("error"), _q("warning")])
    assert folded.overall == "error"


def test_fold_quality_max_age():
    folded = _fold_quality([_q("ok", age=3), _q("ok", age=10), _q("ok", age=2)])
    assert folded.data_age_days == 10


def test_fold_quality_mean_coverage():
    folded = _fold_quality([_q("ok", coverage=0.6), _q("ok", coverage=1.0)])
    assert folded.coverage_pct == 0.8
```

- [ ] **Step 2: Run**

```bash
uv run pytest tests/test_canton.py -v
```

Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/test_canton.py
git commit -m "test(canton): cover quality folding edge cases"
```

---

## Phase 4: YAML Restructure (Spec migration step 4)

### Task 4.1: Rename example-report.yaml → canton-bulletin.yaml

**Files:**
- Rename: `data/ruleset/example-report.yaml` → `data/ruleset/canton-bulletin.yaml`

- [ ] **Step 1: Rename**

```bash
git mv data/ruleset/example-report.yaml data/ruleset/canton-bulletin.yaml
```

- [ ] **Step 2: Commit (rename-only, for diff clarity)**

```bash
git commit -m "refactor(ruleset): rename example-report.yaml to canton-bulletin.yaml"
```

### Task 4.2: Restructure lead block for canton scope

**Files:**
- Modify: `data/ruleset/canton-bulletin.yaml`

- [ ] **Step 1: Replace the `lead` block**

Find the existing `lead:` block in `data/ruleset/canton-bulletin.yaml` and replace it with:

```yaml
lead:
  warnstufe:
    headline:
      de: "{{ canton.max_warnlevel_info_de }}, Stufe {{ canton.max_warnlevel }}"
      fr: "{{ canton.max_warnlevel_info_fr }}, niveau {{ canton.max_warnlevel }}"
    meta:
      de: "Gültig ab {{ format_date(canton.data_timestamp, 'DD.MM.YYYY') }}"
      fr: "Valable à partir du {{ format_date(canton.data_timestamp, 'DD.MM.YYYY') }}"
    farben_pro_stufe:
      1: { hintergrund: "#6bbd50", text: "#ffffff", label: "grün" }
      2: { hintergrund: "#f7e84c", text: "#1a1a1a", label: "gelb" }
      3: { hintergrund: "#ff8c00", text: "#ffffff", label: "orange" }
      4: { hintergrund: "#e02020", text: "#ffffff", label: "rot" }
      5: { hintergrund: "#8b0000", text: "#ffffff", label: "dunkelrot" }
    maps:
      - id: cdi_current
        title: { de: "Aktueller CDI", fr: "CDI actuel" }
        source: "canton.regions[*].cdi"
        style: "choropleth_warnregionen"
      - id: cdi_forecast_week2
        title: { de: "CDI-Prognose Woche 2", fr: "Prévision CDI semaine 2" }
        source: "canton.regions[*].cdi_forecast_week2"
        style: "choropleth_warnregionen"
```

- [ ] **Step 2: Commit**

```bash
git add data/ruleset/canton-bulletin.yaml
git commit -m "refactor(ruleset): canton-level lead block with maps sub-block"
```

### Task 4.3: Add canton-aggregated `allgemeine-lage` section

**Files:**
- Modify: `data/ruleset/canton-bulletin.yaml`

- [ ] **Step 1: Replace the existing `allgemeine-lage` section template**

Find the section with `id: allgemeine-lage` and replace its `template` and `placeholders` with:

```yaml
  - id: allgemeine-lage
    title:
      de: "Allgemeine Lage"
      fr: "Situation générale"
    template:
      de: |
        Im Kanton {{ canton.canton_name_de }} weisen aktuell {{ canton.n_regions_by_precip_index.get(2, 0) + canton.n_regions_by_precip_index.get(3, 0) + canton.n_regions_by_precip_index.get(4, 0) + canton.n_regions_by_precip_index.get(5, 0) }} von {{ canton.regions|length }} Warnregionen ein Niederschlagsdefizit auf.
        Bei der Bodenfeuchte weisen {{ canton.n_regions_by_soil_moisture_index.get(2, 0) + canton.n_regions_by_soil_moisture_index.get(3, 0) + canton.n_regions_by_soil_moisture_index.get(4, 0) + canton.n_regions_by_soil_moisture_index.get(5, 0) }} von {{ canton.regions|length }} Warnregionen ein Defizit auf.
        Die höchste Gefahrenstufe im Kanton ist Stufe {{ canton.max_warnlevel }} ({{ canton.max_warnlevel_info_de }}).
      fr: |
        Dans le canton de {{ canton.canton_name_fr }}, {{ canton.n_regions_by_precip_index.get(2, 0) + canton.n_regions_by_precip_index.get(3, 0) + canton.n_regions_by_precip_index.get(4, 0) + canton.n_regions_by_precip_index.get(5, 0) }} régions d'alerte sur {{ canton.regions|length }} présentent actuellement un déficit pluviométrique.
        Concernant l'humidité du sol, {{ canton.n_regions_by_soil_moisture_index.get(2, 0) + canton.n_regions_by_soil_moisture_index.get(3, 0) + canton.n_regions_by_soil_moisture_index.get(4, 0) + canton.n_regions_by_soil_moisture_index.get(5, 0) }} régions sur {{ canton.regions|length }} présentent un déficit.
        Le niveau d'alerte le plus élevé du canton est le niveau {{ canton.max_warnlevel }} ({{ canton.max_warnlevel_info_fr }}).
    placeholders:
      - id: precip_index_summary
        source: canton.n_regions_by_precip_index
      - id: soil_moisture_summary
        source: canton.n_regions_by_soil_moisture_index
      - id: max_warnlevel_summary
        source: canton.max_warnlevel
```

- [ ] **Step 2: Commit**

```bash
git add data/ruleset/canton-bulletin.yaml
git commit -m "refactor(ruleset): canton-aggregated allgemeine-lage section"
```

### Task 4.4: Add `regionen` iteration section

**Files:**
- Modify: `data/ruleset/canton-bulletin.yaml`

- [ ] **Step 1: Insert a new `regionen` section between `allgemeine-lage` and `handlungsoptionen`**

```yaml
  - id: regionen
    title:
      de: "Allgemeine Lage nach Regionen"
      fr: "Situation par région"
    template:
      de: |
        {{#each canton.regions}}
        ### {{ this.region_name_de }}

        In den vergangenen 30 Tagen sind in der Region {{ this.region_name_de }} rund {{ this.precip_sum_1m }} mm Niederschlag gefallen (3-Monats-Summe: {{ this.precip_sum_3m }} mm). Die Region weist damit aktuell {{ nomenclature.niederschlag.noun[this.precip_1m_index].de }} auf. Es besteht zurzeit {{ nomenclature.bodenfeuchte.noun[this.soil_moisture_index].de }}.

        {{/each}}
      fr: |
        {{#each canton.regions}}
        ### {{ this.region_name_de }}

        Au cours des 30 derniers jours, environ {{ this.precip_sum_1m }} mm de précipitations sont tombés dans la région {{ this.region_name_de }} (cumul sur 3 mois : {{ this.precip_sum_3m }} mm). La région présente actuellement {{ nomenclature.niederschlag.noun[this.precip_1m_index].fr }}. Concernant l'humidité du sol, il y a actuellement {{ nomenclature.bodenfeuchte.noun[this.soil_moisture_index].fr }}.

        {{/each}}
    placeholders:
      - id: region_loop
        source: canton.regions
        description: "Iterate over each region in the canton, render per-region paragraph."
```

- [ ] **Step 2: Commit**

```bash
git add data/ruleset/canton-bulletin.yaml
git commit -m "refactor(ruleset): add regionen iteration section for per-region narrative"
```

### Task 4.5: Update handlungsoptionen and datenquellen for canton context

**Files:**
- Modify: `data/ruleset/canton-bulletin.yaml`

- [ ] **Step 1: Replace `handlungsoptionen.template`**

```yaml
  - id: handlungsoptionen
    title:
      de: "Handlungsoptionen"
      fr: "Options d'action"
    template:
      de: |
        {{#each handlungsempfehlungen.by_gefahrenstufe[canton.max_warnlevel].empfehlungen.de}}
        - {{ this }}
        {{/each}}
      fr: |
        {{#each handlungsempfehlungen.by_gefahrenstufe[canton.max_warnlevel].empfehlungen.fr}}
        - {{ this }}
        {{/each}}
    placeholders:
      - id: max_warnlevel
        source: canton.max_warnlevel
        resolver: handlungsempfehlungen.by_gefahrenstufe
        fallback_rule: "If recommendations missing for a level, follow .fallback chain (3 → 2, 5 → 4)."
```

- [ ] **Step 2: Update top-level `context` block**

Replace (or insert near top) the `context:` block:

```yaml
context:
  scope: canton
  required_inputs:
    canton_id: "BFS canton ID (e.g. 2 for Bern)"
```

- [ ] **Step 3: Commit**

```bash
git add data/ruleset/canton-bulletin.yaml
git commit -m "refactor(ruleset): handlungsoptionen and context use canton scope"
```

### Task 4.6: Port French recommendation strings into the YAML

**Files:**
- Modify: `data/ruleset/canton-bulletin.yaml`

- [ ] **Step 1: Read the FR recommendation strings**

```bash
cat src/briefing/text_blocks_fr.py
```

Note the bullet-list French strings used per CDI level.

- [ ] **Step 2: Add `fr` lists to `handlungsempfehlungen.by_gefahrenstufe`**

Replace the existing `handlungsempfehlungen` block (keep the existing `source_ref` line). Set all three populated levels (1, 2, 4) with both `de` and `fr` arrays. Levels 3 and 5 remain `fallback`-only. The FR strings here are the official BAFU translations from `https://www.trockenheit.admin.ch/fr/...`; if `src/briefing/text_blocks_fr.py` already contains alternative phrasings, prefer the BAFU originals below.

```yaml
handlungsempfehlungen:
  source_ref: references.handlungsempfehlungen_bafu
  by_gefahrenstufe:
    1:
      empfehlungen:
        de:
          - "Es sind keine besonderen Massnahmen zur Vorbeugung von Trockenheit erforderlich."
        fr:
          - "Aucune mesure particulière n'est nécessaire pour prévenir la sécheresse."
    2:
      empfehlungen:
        de:
          - "Informieren Sie sich auf www.trockenheit.ch über die aktuelle Lage in Ihrer Region."
          - "Informieren Sie sich über mögliche Einschränkungen der Wassernutzung."
          - "Gehen Sie sparsam mit den Wasserressourcen um."
        fr:
          - "Informez-vous sur www.trockenheit.ch sur la situation actuelle dans votre région."
          - "Informez-vous sur les éventuelles restrictions d'utilisation de l'eau."
          - "Utilisez les ressources en eau avec parcimonie."
    3:
      fallback: 2
    4:
      empfehlungen:
        de:
          - "Informieren Sie sich über mögliche Anweisungen der lokalen Behörden betreffend Verbote und Einschränkungen der Wassernutzung und beachten Sie diese."
          - "Gehen Sie sparsam mit den Wasserressourcen um."
          - "Halten Sie sich an die Anweisungen und Verbote der lokalen Behörden bezüglich Waldbrandgefahr."
        fr:
          - "Informez-vous sur les éventuelles consignes des autorités locales concernant les interdictions et restrictions d'utilisation de l'eau et respectez-les."
          - "Utilisez les ressources en eau avec parcimonie."
          - "Respectez les consignes et interdictions des autorités locales concernant les risques d'incendie de forêt."
    5:
      fallback: 4
```

- [ ] **Step 3: Verify YAML still parses**

```bash
uv run python -c "import yaml; yaml.safe_load(open('data/ruleset/canton-bulletin.yaml'))"
```

Expected: No error.

- [ ] **Step 4: Commit**

```bash
git add data/ruleset/canton-bulletin.yaml
git commit -m "refactor(ruleset): port FR recommendation strings from text_blocks_fr"
```

---

## Phase 5: Ruleset Schema + Loader (Spec migration step 5)

### Task 5.1: Pydantic schema for the ruleset

**Files:**
- Create: `src/briefing/schemas.py`
- Create: `tests/test_renderer.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_renderer.py
from pathlib import Path
from src.briefing.schemas import RulesetSchema
from src.briefing.renderer import load_ruleset


RULESET_PATH = Path("data/ruleset/canton-bulletin.yaml")


def test_load_ruleset_returns_schema_instance():
    ruleset = load_ruleset(RULESET_PATH)
    assert isinstance(ruleset, RulesetSchema)
    assert ruleset.id == "example-report"  # id field still says this; will be renamed in later commit if needed
    assert "warnkarte" in ruleset.data_sources
    assert "niederschlag" in ruleset.nomenclature.indicators
```

- [ ] **Step 2: Run to see it fail**

```bash
uv run pytest tests/test_renderer.py::test_load_ruleset_returns_schema_instance -v
```

Expected: FAIL — modules missing.

- [ ] **Step 3: Write the schema**

```python
# src/briefing/schemas.py
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ContextSpec(BaseModel):
    scope: str
    required_inputs: dict[str, str] = Field(default_factory=dict)
    model_config = ConfigDict(extra="forbid")


class DataSourceSpec(BaseModel):
    type: str
    provider: str
    title: str
    url: str | None = None
    landing_page: str | None = None
    response_path: str | None = None
    fields: dict[str, str] | None = None
    description: str | None = None
    datasets_used: list[str] | None = None
    model_config = ConfigDict(extra="forbid")


class ReferenceSpec(BaseModel):
    title: str
    url: str
    provider: str
    model_config = ConfigDict(extra="forbid")


class NomenclatureIndicatorSpec(BaseModel):
    field: str | None = None
    fields: list[str] | None = None
    scope: str | None = None
    note: str | None = None
    adjective: dict[int, dict[str, str]] | None = None
    noun: dict[int, dict[str, str]] | None = None
    model_config = ConfigDict(extra="forbid")


class NomenclatureSpec(BaseModel):
    indicators: dict[str, NomenclatureIndicatorSpec]


class TrendSpec(BaseModel):
    rule: str
    stable_tolerance: float
    increase: dict[str, str]
    decrease: dict[str, str]
    stable: dict[str, str]
    model_config = ConfigDict(extra="forbid")


class HandlungsempfehlungenLevel(BaseModel):
    empfehlungen: dict[str, list[str]] | None = None
    fallback: int | None = None
    model_config = ConfigDict(extra="forbid")


class HandlungsempfehlungenSpec(BaseModel):
    source_ref: str
    by_gefahrenstufe: dict[int, HandlungsempfehlungenLevel]
    model_config = ConfigDict(extra="forbid")


class MapSpec(BaseModel):
    id: str
    title: dict[str, str]
    source: str
    style: str
    model_config = ConfigDict(extra="forbid")


class LeadWarnstufe(BaseModel):
    headline: dict[str, str]
    meta: dict[str, str]
    farben_pro_stufe: dict[int, dict[str, str]]
    maps: list[MapSpec]
    placeholders: list[dict[str, Any]] | None = None
    model_config = ConfigDict(extra="forbid")


class LeadSpec(BaseModel):
    warnstufe: LeadWarnstufe
    model_config = ConfigDict(extra="forbid")


class SectionSpec(BaseModel):
    id: str
    title: dict[str, str]
    locale: str | None = None
    template: dict[str, str]
    placeholders: list[dict[str, Any]] | None = None
    notes: list[str] | None = None
    model_config = ConfigDict(extra="forbid")


class RulesetSchema(BaseModel):
    id: str
    title: str
    description: str | None = None
    context: ContextSpec
    data_sources: dict[str, DataSourceSpec]
    references: dict[str, ReferenceSpec]
    nomenclature: NomenclatureSpec
    trend: dict[str, TrendSpec]
    handlungsempfehlungen: HandlungsempfehlungenSpec
    lead: LeadSpec
    sections: list[SectionSpec]
    model_config = ConfigDict(extra="forbid")
```

- [ ] **Step 4: Create the loader stub**

```python
# src/briefing/renderer.py
from __future__ import annotations

from pathlib import Path

import yaml

from src.briefing.schemas import RulesetSchema, NomenclatureSpec, NomenclatureIndicatorSpec


def load_ruleset(path: Path) -> RulesetSchema:
    """Load YAML, validate via Pydantic, return the schema object."""
    raw = yaml.safe_load(path.read_text())

    # NomenclatureSpec wraps the raw mapping under an `indicators` key for type clarity.
    if "nomenclature" in raw and "indicators" not in raw["nomenclature"]:
        raw["nomenclature"] = {"indicators": raw["nomenclature"]}

    return RulesetSchema.model_validate(raw)
```

- [ ] **Step 5: Run the test**

```bash
uv run pytest tests/test_renderer.py::test_load_ruleset_returns_schema_instance -v
```

Expected: PASS. If it fails because of an unknown field in the YAML, fix the YAML or extend the schema — do not relax `extra="forbid"`.

- [ ] **Step 6: Commit**

```bash
git add src/briefing/schemas.py src/briefing/renderer.py tests/test_renderer.py
git commit -m "feat(briefing): add Pydantic ruleset schema and YAML loader"
```

---

## Phase 6: Renderer (Spec migration step 6)

### Task 6.1: Handlebars → Jinja2 preprocessor

**Files:**
- Modify: `src/briefing/renderer.py`
- Modify: `tests/test_renderer.py`

- [ ] **Step 1: Write the test**

Append to `tests/test_renderer.py`:

```python
from src.briefing.renderer import _handlebars_to_jinja2


def test_handlebars_each_block_converted():
    src = "{{#each items}}- {{ this.name }}\n{{/each}}"
    out = _handlebars_to_jinja2(src)
    assert "{% for item in items %}" in out
    assert "{{ item.name }}" in out
    assert "{% endfor %}" in out


def test_handlebars_no_each_unchanged():
    src = "Hello {{ canton.canton_name_de }}."
    assert _handlebars_to_jinja2(src) == src
```

- [ ] **Step 2: Run, see it fail**

```bash
uv run pytest tests/test_renderer.py -v -k handlebars
```

Expected: FAIL.

- [ ] **Step 3: Implement the preprocessor**

In `src/briefing/renderer.py`, append:

```python
import re

_EACH_OPEN = re.compile(r"\{\{#each\s+([^\s}]+)\s*\}\}")
_EACH_CLOSE = re.compile(r"\{\{/each\}\}")
_THIS_FIELD = re.compile(r"\{\{\s*this\.([^\s}]+)\s*\}\}")


def _handlebars_to_jinja2(src: str) -> str:
    src = _EACH_OPEN.sub(r"{% for item in \1 %}", src)
    src = _EACH_CLOSE.sub("{% endfor %}", src)
    src = _THIS_FIELD.sub(r"{{ item.\1 }}", src)
    return src
```

- [ ] **Step 4: Run**

```bash
uv run pytest tests/test_renderer.py -v -k handlebars
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add src/briefing/renderer.py tests/test_renderer.py
git commit -m "feat(renderer): add handlebars-to-jinja2 preprocessor"
```

### Task 6.2: render_briefing() — happy path with format_date and lookup

**Files:**
- Modify: `src/briefing/renderer.py`
- Modify: `tests/test_renderer.py`

- [ ] **Step 1: Write the failing test**

Append:

```python
from datetime import datetime

from src.aggregation.canton import compute_canton_report
from src.briefing.renderer import render_briefing
from src.data.stac_client import load as load_data
from src.models import WarnkarteEntry


def test_render_briefing_de_section_keys():
    bundle = load_data()
    warnkarte = {
        rid: WarnkarteEntry(
            drought_region_id=rid,
            warnlevel=2,
            info_de="Mässige Gefahr",
            info_fr="Danger limité",
            info_it="-",
            valid_from=datetime(2026, 5, 28),
        )
        for rid in [33, 34, 35, 37, 38, 41]
    }
    canton = compute_canton_report(canton_id=2, bundle=bundle, warnkarte_data=warnkarte)
    ruleset = load_ruleset(RULESET_PATH)

    doc = render_briefing(canton, ruleset, locale="de")

    assert set(doc.sections.keys()) >= {"allgemeine-lage", "handlungsoptionen", "regionen"}
    assert "Bern" in doc.sections["allgemeine-lage"]
    assert "Mässige Gefahr" in doc.sections["allgemeine-lage"]
    # Maps spec preserved
    assert len(doc.lead_maps) == 2
    assert {m.id for m in doc.lead_maps} == {"cdi_current", "cdi_forecast_week2"}
```

- [ ] **Step 2: Update `BriefingDocument`**

In `src/models.py`, extend `BriefingDocument`:

```python
@dataclass
class BriefingDocument:
    sections: dict[str, str]
    report: object                     # CantonReport (avoid forward-ref import for now)
    locale: str
    generated_at: datetime
    lead_maps: list = field(default_factory=list)   # list[MapSpec]
    lead_headline: str = ""
    lead_meta: str = ""
```

Add `from dataclasses import field` to the imports.

- [ ] **Step 3: Implement `render_briefing`**

In `src/briefing/renderer.py`:

```python
from datetime import datetime
from typing import Literal

from jinja2 import BaseLoader, Environment, StrictUndefined

from src.models import BriefingDocument, CantonReport, MapSpec


def _format_date(value: datetime | str, pattern: str) -> str:
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    mapping = {
        "DD.MM.YYYY": value.strftime("%d.%m.%Y"),
        "YYYY-MM-DD": value.strftime("%Y-%m-%d"),
    }
    return mapping.get(pattern, value.strftime(pattern))


def _make_trend_resolver(trend_spec, locale: str):
    def trend(delta, key):
        spec = trend_spec[key]
        if abs(delta) <= spec.stable_tolerance:
            return spec.stable[locale]
        return (spec.increase if delta > 0 else spec.decrease)[locale]
    return trend


def render_briefing(
    canton: CantonReport,
    ruleset: RulesetSchema,
    locale: Literal["de", "fr"] = "de",
) -> BriefingDocument:
    env = Environment(
        loader=BaseLoader(),
        undefined=StrictUndefined,
        autoescape=False,
    )
    env.filters["format_date"] = _format_date
    env.globals["format_date"] = _format_date
    env.globals["trend"] = _make_trend_resolver(ruleset.trend, locale)
    env.globals["nomenclature"] = ruleset.nomenclature.indicators
    env.globals["handlungsempfehlungen"] = ruleset.handlungsempfehlungen
    env.globals["canton"] = canton

    sections: dict[str, str] = {}
    for sec in ruleset.sections:
        tmpl_src = _handlebars_to_jinja2(sec.template[locale])
        sections[sec.id] = env.from_string(tmpl_src).render().strip()

    # Lead
    lead = ruleset.lead.warnstufe
    headline = env.from_string(_handlebars_to_jinja2(lead.headline[locale])).render()
    meta = env.from_string(_handlebars_to_jinja2(lead.meta[locale])).render()
    lead_maps = [
        MapSpec(
            id=m.id,
            title_de=m.title.get("de", ""),
            title_fr=m.title.get("fr", ""),
            source=m.source,
            style=m.style,
        )
        for m in lead.maps
    ]

    return BriefingDocument(
        sections=sections,
        report=canton,
        locale=locale,
        generated_at=datetime.now(),
        lead_maps=lead_maps,
        lead_headline=headline,
        lead_meta=meta,
    )
```

- [ ] **Step 4: Run the test**

```bash
uv run pytest tests/test_renderer.py -v
```

Expected: PASS. If a Jinja2 `UndefinedError` surfaces (missing field), inspect the template, fix the YAML or field name, and re-run.

- [ ] **Step 5: Commit**

```bash
git add src/briefing/renderer.py src/models.py tests/test_renderer.py
git commit -m "feat(renderer): render_briefing with Jinja2 environment and lead-map specs"
```

### Task 6.3: Snapshot test for FR locale

**Files:**
- Modify: `tests/test_renderer.py`

- [ ] **Step 1: Write the test**

```python
def test_render_briefing_fr_uses_french_strings():
    bundle = load_data()
    warnkarte = {
        rid: WarnkarteEntry(
            drought_region_id=rid,
            warnlevel=2,
            info_de="Mässige Gefahr",
            info_fr="Danger limité",
            info_it="-",
            valid_from=datetime(2026, 5, 28),
        )
        for rid in [33, 34, 35, 37, 38, 41]
    }
    canton = compute_canton_report(canton_id=2, bundle=bundle, warnkarte_data=warnkarte)
    ruleset = load_ruleset(RULESET_PATH)

    doc = render_briefing(canton, ruleset, locale="fr")

    assert "Berne" in doc.sections["allgemeine-lage"]
    assert "Danger limité" in doc.sections["allgemeine-lage"]
```

- [ ] **Step 2: Run**

```bash
uv run pytest tests/test_renderer.py::test_render_briefing_fr_uses_french_strings -v
```

Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add tests/test_renderer.py
git commit -m "test(renderer): cover FR locale rendering"
```

---

## Phase 7: Maps (Spec migration step 7)

### Task 7.1: build_canton_map for current CDI

**Files:**
- Modify: `src/viz/maps.py`

- [ ] **Step 1: Add function**

In `src/viz/maps.py`, append:

```python
from src.models import CantonReport, MapSpec


def build_canton_map(canton: CantonReport, map_spec: MapSpec):
    """
    Folium map showing CDI per warning region of the canton.
    Dispatches on map_spec.id: "cdi_current" uses RegionReport.cdi;
    "cdi_forecast_week2" uses RegionReport.cdi_forecast_week2.
    """
    if map_spec.id == "cdi_current":
        values = {r.region_id: r.cdi for r in canton.regions}
    elif map_spec.id == "cdi_forecast_week2":
        values = {
            r.region_id: r.cdi_forecast_week2 if r.cdi_forecast_week2 is not None else 0
            for r in canton.regions
        }
    else:
        raise ValueError(f"Unknown map id: {map_spec.id}")

    # Reuse the existing folium-building helper.
    # This stub mirrors the existing build_map's region-by-region colouring
    # — concrete implementation follows the existing pattern.
    return _build_folium_choropleth(values)


def _build_folium_choropleth(values: dict[int, int]):
    """Render values dict as folium choropleth using the bundled geojson."""
    import json
    import folium
    from config.settings import CDI_COLOURS, GEOJSON_FIXTURE

    geo = json.loads(GEOJSON_FIXTURE.read_text())
    m = folium.Map(location=[46.8, 7.4], zoom_start=8, tiles="cartodbpositron")

    def style_fn(feature):
        rid = int(feature["properties"]["idn"])
        cdi = values.get(rid, 0)
        return {
            "fillColor": CDI_COLOURS.get(cdi, "#cccccc"),
            "color": "#333",
            "weight": 1,
            "fillOpacity": 0.75,
        }

    folium.GeoJson(geo, style_function=style_fn).add_to(m)
    return m
```

- [ ] **Step 2: Smoke-test the function manually (no pytest yet)**

```bash
uv run python - <<'PY'
from datetime import datetime
from src.aggregation.canton import compute_canton_report
from src.data.stac_client import load
from src.models import WarnkarteEntry
from src.viz.maps import build_canton_map
from src.briefing.schemas import MapSpec as _SchemaMapSpec
from src.models import MapSpec

bundle = load()
warn = {rid: WarnkarteEntry(rid, 2, "Mässige Gefahr", "Danger limité", "-", datetime(2026, 5, 28))
        for rid in [33, 34, 35, 37, 38, 41]}
canton = compute_canton_report(canton_id=2, bundle=bundle, warnkarte_data=warn)
m = build_canton_map(canton, MapSpec(id="cdi_current", title_de="x", title_fr="x", source="-", style="choropleth_warnregionen"))
print("OK", type(m).__name__)
PY
```

Expected: prints `OK Map`.

- [ ] **Step 3: Commit**

```bash
git add src/viz/maps.py
git commit -m "feat(viz): add build_canton_map for current and forecast CDI"
```

---

## Phase 8: app.py Rewire (Spec migration step 8)

### Task 8.1: Replace mode selector with canton selector

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Remove the mode radio block**

In `app.py`, locate the `mode = st.radio(...)` block in the sidebar and delete it.

- [ ] **Step 2: Replace the region selectbox with a canton selectbox**

Replace the existing region-selectbox block with:

```python
from config.settings import CANTON_NAMES, CANTON_TO_REGIONS

canton_options = sorted(CANTON_TO_REGIONS.keys())
selected_canton_id = st.selectbox(
    "Kanton",
    options=canton_options,
    format_func=lambda cid: CANTON_NAMES[cid].get(lang, CANTON_NAMES[cid]["de"]),
    index=0,
)
```

(`lang` is the existing language-toggle variable from main.)

- [ ] **Step 3: Smoke-test by reloading the browser**

The Streamlit dev server should auto-reload. Verify the sidebar shows only one selector (canton), no mode radio.

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "feat(app): replace mode + region selectors with canton selector"
```

### Task 8.2: Wire canton pipeline

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Replace the pipeline call**

Find:
```python
all_reports = [compute_region_report(rid, bundle) for rid in BERNE_REGION_IDS]
report = next(r for r in all_reports if r.region_id == selected_region_id)
doc = build_briefing(report, mode)
```

Replace with:

```python
from src.aggregation.canton import compute_canton_report
from src.briefing.renderer import load_ruleset, render_briefing
from src.data.warnkarte_client import fetch_for_regions

@st.cache_data(ttl=3600, show_spinner="Warnstufen werden geladen…")
def _load_warnkarte(region_ids: tuple[int, ...]):
    return fetch_for_regions(list(region_ids))

@st.cache_resource
def _ruleset():
    return load_ruleset(Path("data/ruleset/canton-bulletin.yaml"))

region_ids = tuple(sorted(CANTON_TO_REGIONS[selected_canton_id]))
warnkarte = _load_warnkarte(region_ids)
canton = compute_canton_report(
    canton_id=selected_canton_id,
    bundle=bundle,
    warnkarte_data=warnkarte,
)
doc = render_briefing(canton, _ruleset(), locale=lang)
```

Add `from pathlib import Path` and remove the now-unused `from src.briefing.template import build_briefing`.

- [ ] **Step 2: Verify in the browser**

Reload. Expect: no errors. The page still renders, with new data sources wired.

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat(app): wire canton pipeline with warnkarte + ruleset renderer"
```

### Task 8.3: Render lead box + two maps

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Replace the header/badge block with the lead box**

Find the existing header `col_title, col_badge = st.columns([4, 1])` block and replace it with:

```python
st.title(f"Trockenheitsbriefing {canton.canton_name_de if lang == 'de' else canton.canton_name_fr}")
st.markdown(
    f"""<div style="background:{ruleset_warnstufe_colour(canton.max_warnlevel)};border-radius:8px;padding:18px;color:#fff;">
    <div style="font-size:11px;opacity:.85;">{('Aktuelle Warnstufe' if lang=='de' else 'Niveau actuel')}</div>
    <div style="font-size:28px;font-weight:700;">{doc.lead_headline}</div>
    <div style="font-size:12px;opacity:.85;">{doc.lead_meta}</div>
    </div>""",
    unsafe_allow_html=True,
)

def ruleset_warnstufe_colour(level: int) -> str:
    palette = {1: "#6bbd50", 2: "#f7e84c", 3: "#ff8c00", 4: "#e02020", 5: "#8b0000"}
    return palette.get(level, "#cccccc")
```

Move the `ruleset_warnstufe_colour` definition above the markdown call.

- [ ] **Step 2: Render the two maps side by side**

```python
from src.viz.maps import build_canton_map

map_cols = st.columns(2)
for col, map_spec in zip(map_cols, doc.lead_maps):
    with col:
        st.subheader(map_spec.title_de if lang == "de" else map_spec.title_fr)
        m = build_canton_map(canton, map_spec)
        st.components.v1.html(m._repr_html_(), height=300)
```

- [ ] **Step 3: Verify in the browser**

The page should now show the lead box + two side-by-side maps. The colour reflects `canton.max_warnlevel`.

- [ ] **Step 4: Commit**

```bash
git add app.py
git commit -m "feat(app): render canton lead box and CDI/forecast maps"
```

### Task 8.4: Render text sections from the new doc.sections

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Replace the sections loop**

Find the existing `for section_key, section_title in [...]:` block and replace it with:

```python
from src.briefing.schemas import SectionSpec  # for type hint only

for sec in _ruleset().sections:
    title = sec.title.get(lang, sec.title.get("de", sec.id))
    st.markdown(f"## {title}")
    st.markdown(doc.sections[sec.id])
    st.write("")
```

- [ ] **Step 2: Verify in the browser**

Three section headings should render: Allgemeine Lage, Allgemeine Lage nach Regionen, Handlungsoptionen, Datenquellen (matching the YAML sections order).

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat(app): render text sections from new ruleset doc"
```

### Task 8.5: Canton-aware quality panel

**Files:**
- Modify: `app.py`

- [ ] **Step 1: Replace the quality expander**

Find the existing `with st.expander("Qualität & Datengrundlage"):` block. Replace its body with:

```python
with st.expander(t("quality_expander", lang)):
    q = canton.quality
    q_colour = {"ok": "🟢", "warning": "🟡", "error": "🔴"}.get(q.overall, "⚪")
    st.markdown(
        f"{q_colour} **{q.overall.upper()}** — "
        f"{t('data_age', lang)}: {q.data_age_days} {t('days', lang)} — "
        f"{t('coverage', lang)}: {q.coverage_pct:.0%}"
    )
    if q.missing_columns:
        st.warning(f"{t('quality_missing_cols', lang)}: {', '.join(q.missing_columns)}")
    if q.outlier_flags:
        st.warning(f"{t('quality_outliers', lang)}: {', '.join(q.outlier_flags)}")
    # Per-region drill-down
    for r in canton.regions:
        st.caption(
            f"R{r.region_id} ({r.region_name_de}): "
            f"{r.quality.overall} — coverage {r.quality.coverage_pct:.0%}"
        )
```

If keys like `days` or `quality_outliers` are not in `src/i18n/strings.py`, add them with DE+FR translations.

- [ ] **Step 2: Verify**

Reload, expand the quality panel. Expect: canton-aggregated overall, plus per-region drill-down lines.

- [ ] **Step 3: Commit**

```bash
git add app.py src/i18n/strings.py
git commit -m "feat(app): canton-aware quality panel with per-region drill-down"
```

### Task 8.6: Update HTML export to take CantonReport

**Files:**
- Modify: `src/export/report.py`
- Modify: `tests/test_export.py`

- [ ] **Step 1: Read the existing `to_html` to find the function boundaries**

```bash
sed -n '1,80p' src/export/report.py
```

The existing function is a single block that returns an HTML string from a `RegionReport` + chart PNG + map PNG. We rewrite it to take a `CantonReport` and the new `BriefingDocument` (with `lead_headline`, `lead_meta`, and `sections`).

- [ ] **Step 2: Replace the `to_html` function**

Locate `def to_html(...)` and replace it (and any helper that references `report.region_name_de`) with:

```python
def to_html(
    doc: "BriefingDocument",
    canton_report: "CantonReport",
    chart_fig=None,
    map_png: bytes | None = None,
) -> str:
    title = f"Trockenheitsbriefing {canton_report.canton_name_de}"
    badge_colour = {
        1: "#6bbd50", 2: "#f7e84c", 3: "#ff8c00", 4: "#e02020", 5: "#8b0000",
    }.get(canton_report.max_warnlevel, "#cccccc")
    badge_html = (
        f'<div style="background:{badge_colour};color:#fff;padding:14px;border-radius:6px;">'
        f'<div style="font-size:24px;font-weight:700;">{doc.lead_headline}</div>'
        f'<div style="font-size:11px;opacity:.85;">{doc.lead_meta}</div>'
        f'</div>'
    )
    sections_html = "\n".join(
        f'<section><h2>{sec_id}</h2><div>{body}</div></section>'
        for sec_id, body in doc.sections.items()
    )
    return f"""<!DOCTYPE html>
<html lang="{doc.locale}">
<head><meta charset="UTF-8"><title>{title}</title></head>
<body>
<header><h1>{title}</h1>{badge_html}</header>
<main>{sections_html}</main>
</body>
</html>"""
```

Add `from src.models import BriefingDocument, CantonReport` at the top if not present (or use string annotations as shown above).

- [ ] **Step 3: Rewrite the export test**

Replace the body of `tests/test_export.py` with:

```python
from datetime import datetime

from src.aggregation.canton import compute_canton_report
from src.briefing.renderer import load_ruleset, render_briefing
from src.data.stac_client import load as load_data
from src.export.report import to_html
from src.models import WarnkarteEntry
from pathlib import Path


def test_to_html_contains_canton_name_and_sections():
    bundle = load_data()
    warnkarte = {
        rid: WarnkarteEntry(
            drought_region_id=rid,
            warnlevel=2,
            info_de="Mässige Gefahr",
            info_fr="Danger limité",
            info_it="-",
            valid_from=datetime(2026, 5, 28),
        )
        for rid in [33, 34, 35, 37, 38, 41]
    }
    canton = compute_canton_report(canton_id=2, bundle=bundle, warnkarte_data=warnkarte)
    ruleset = load_ruleset(Path("data/ruleset/canton-bulletin.yaml"))
    doc = render_briefing(canton, ruleset, locale="de")

    html = to_html(doc, canton)

    assert "Bern" in html
    assert "Mässige Gefahr" in html
    assert "allgemeine-lage" in html
```

- [ ] **Step 3: Run tests**

```bash
uv run pytest tests/test_export.py -v
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add src/export/report.py tests/test_export.py
git commit -m "refactor(export): to_html now takes CantonReport"
```

---

## Phase 9: Cleanup (Spec migration step 9)

### Task 9.1: Delete legacy text-block modules

**Files:**
- Delete: `src/briefing/text_blocks_de.py`
- Delete: `src/briefing/text_blocks_fr.py`
- Delete: `src/briefing/template.py`
- Delete: `tests/test_text_blocks.py`
- Delete: `tests/test_briefing_fr.py`

- [ ] **Step 1: Delete the files**

```bash
git rm src/briefing/text_blocks_de.py src/briefing/text_blocks_fr.py src/briefing/template.py
git rm tests/test_text_blocks.py tests/test_briefing_fr.py
```

- [ ] **Step 2: Run the full test suite**

```bash
uv run pytest tests/ -v
```

Expected: PASS. If any test still imports from the deleted modules, fix or delete it. The new tests we wrote should pass; the deleted-file tests should no longer be collected.

- [ ] **Step 3: Commit**

```bash
git commit -m "chore: delete legacy text_blocks and template modules"
```

### Task 9.2: Delete BERNE_REGION_IDS and _TREND_LABELS leftovers

**Files:**
- Modify: `config/settings.py`
- Modify: `app.py`

- [ ] **Step 1: Remove the constants**

In `config/settings.py`, delete `BERNE_REGION_IDS` and `BERNE_REGION_NAMES` (also `BERNE_REGION_NAMES_FR` from main) — they are now subsumed by `CANTON_TO_REGIONS` and `CANTON_NAMES`. Also delete `CDI_LABELS`, `CDI_LABELS_FR` if they are unused (verify via grep). Keep `CDI_COLOURS` (still used by maps).

- [ ] **Step 2: Remove the imports from app.py**

```bash
grep -n "BERNE_REGION" app.py config/settings.py src/
```

Expected: no remaining references in code (only in tests' historical assertions, which were already updated).

- [ ] **Step 3: Run tests**

```bash
uv run pytest tests/ -v
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add config/settings.py app.py
git commit -m "chore: remove legacy BERNE_REGION_IDS and unused labels"
```

### Task 9.3: Final manual verification

- [ ] **Step 1: Restart the dev server fresh**

```bash
pkill -f "streamlit run app.py" || true
uv run streamlit run app.py
```

- [ ] **Step 2: Open browser to localhost:8501**

Visual checks:
- Sidebar shows: language toggle (de/fr), canton selector (Bern only), no mode radio
- Header: "Trockenheitsbriefing Bern" + coloured warnstufe box (DE) / "Briefing sécheresse Berne" (FR)
- Two maps side by side: current CDI + forecast week 2
- Section headings: Allgemeine Lage / Allgemeine Lage nach Regionen / Handlungsoptionen / Datenquellen
- Quality expander expands and shows canton-aggregated overall + per-region drill-down

- [ ] **Step 3: Toggle language to FR**

Re-verify the same elements in French.

- [ ] **Step 4: Trigger BAFU API live call (clear cache)**

```bash
# In a terminal, while the app runs:
rm -rf ~/.streamlit/cache/  # or use Streamlit's "clear cache" button
```

Re-fetch a page. Expect: warnstufe box still shows the right level (live API).

- [ ] **Step 5: Verify fixture fallback**

Temporarily make the BAFU endpoint unreachable (e.g. block via `/etc/hosts`), reload. Expect: page still renders with values from `data/warnkarte_fixture.json` and a warning is logged.

- [ ] **Step 6: Export the HTML report**

Click "HTML exportieren". Open the downloaded file in a browser. Expect: CDI maps embedded, canton name in title, sections present.

- [ ] **Step 7: Run the full test suite one more time**

```bash
uv run pytest tests/ -v
```

Expected: full PASS.

- [ ] **Step 8: Commit a no-op marker (optional, for branch tag)**

```bash
git commit --allow-empty -m "chore: ruleset integration & canton restructure complete"
```

---

## Done

Branch is ready for PR. Push and open a pull request targeting `main`.

```bash
git push -u origin ruleset-integration
gh pr create --title "feat: integrate YAML ruleset and switch to per-canton scope" \
    --body "Implements spec docs/superpowers/specs/2026-05-28-ruleset-integration-design.md following plan docs/superpowers/plans/2026-05-28-ruleset-integration.md."
```
