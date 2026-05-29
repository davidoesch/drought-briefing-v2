# Canton bulletin template revision — design

Date: 2026-05-29
Status: approved (brainstorming)

## Goal

Integrate the revised text blocks from `data/ruleset/new_template.md` into
`data/ruleset/canton-bulletin.yaml`, and back every new placeholder with a
correct calculation in the typed pipeline. New content adds station-level
discharge statistics, a canton-level CDI situation trend, mean precipitation,
deficit ranges, per-region deficit trends, and several link blocks.

Architecture decision: **extend the existing typed pipeline**
(`DataBundle → RegionReport → CantonReport → renderer`). Logic lives in Python;
all human-readable text stays in the YAML ruleset. Heavy arithmetic currently
inlined in the `allgemeine-lage` template is moved into computed `CantonReport`
fields.

## Semantic decisions (from brainstorming)

- **Mean precipitation** is the mean of `precip_sum_1m` / `precip_sum_3m` over
  the canton's warning regions (region-level data). Stations carry only
  discharge / water level, never precipitation.
- **Precip "langjähriger Vergleich" range**: min and max of `precip_1m_index`
  across the canton's regions, rendered as a nomenclature range, e.g.
  "ein leichtes bis grosses Niederschlagsdefizit".
- **Dry-region range**: regions with `cdi > 1`; min/max CDI among *those* regions
  rendered with `cdi.adjective`, e.g. "leicht trocken bis sehr trocken".
- **Discharge bands**: a discharge station is *low* when its current 7-day value
  `< threshold1` (at the current day-of-year), and *very low* when `< q347`.
  Only stations with `label == "Abfluss"`. `q347` ⊂ low.
- **Forecast horizon** for all trends: week 2 (≈ data date + 14 days), the same
  row selection already used by `_compute_cdi_forecast_week2`.
- **Canton CDI situation trend**: `delta = sum(forecast cdi) − sum(current cdi)`
  across regions. `delta > 0` → verschlechtern, `delta < 0` → verbessern,
  `delta == 0` → unverändert (exact, no tolerance band).
- **Missing per-region forecast** → deficit trend treated as `0` (unverändert);
  the trend sentence still renders.
- **Zero discharge stations** in a region/canton → render an explicit phrase
  ("In dieser Region gibt es keine Abflussmessstationen." / canton variant)
  instead of the percentage sentence. Text lives in the YAML.
- **Links** are new ruleset blocks: a top `banner` block plus a
  `weiterführende_links` block referenced inside `allgemeine-lage`. The
  Grundwasser link is canton-keyed (Bern only for now).

## Part 1 — Data loading & models

### `config/settings.py`
Add constants:
- `CURRENT_STATIONS_CSV = "weekly_current_stations.csv"`
- `REFERENCE_STATIONS_CSV = "daily_reference_stations.csv"`
- `STATION_REGION_MAP_NAME = "station_region_mapping.json"`

### `src/models.py`
`DataBundle` gains (all defaulting to empty so existing construction stays valid):
- `current_stations_df: pd.DataFrame = field(default_factory=pd.DataFrame)`
- `reference_stations_df: pd.DataFrame = field(default_factory=pd.DataFrame)`
- `station_region_map: dict[str, int] = field(default_factory=dict)`

New dataclass:
```python
@dataclass
class DischargeStats:
    n_total: int      # discharge stations with a usable reference row
    n_low: int        # current value < threshold1
    n_very_low: int   # current value < q347  (subset of n_low)
    pct_low: int      # round(n_low / n_total * 100); 0 when n_total == 0
```

### `src/data/fixture_loader.py`
- Read `weekly_current_stations.csv` from the current ZIP and
  `daily_reference_stations.csv` from the reference ZIP via `_read_csv_from_zip`.
  Force `hydro_station_id` to `str` (leading-zero IDs like `"0078"` must match
  the JSON keys). Parse `measured_at` as `DD.MM.YYYY`.
- Load `station_region_mapping.json` from `DATA_DIR` into `station_region_map`
  (`{station_id_str: drought_region_id_int}`).
- Populate the three new `DataBundle` fields. The STAC fallback path is
  unchanged.

## Part 2 — Aggregation

### New module `src/aggregation/stations.py`
Pure, no Streamlit.
```python
def compute_discharge_stats(region_ids: Collection[int], bundle: DataBundle) -> DischargeStats
```
- Select current rows with `label == "Abfluss"` whose
  `station_region_map[id] ∈ region_ids`.
- For each station: derive `doy` from `measured_at`; join to
  `reference_stations_df` on (`hydro_station_id`, `doy`, `label == "Abfluss"`).
  Skip stations with no matching reference row (not counted in `n_total`).
- `n_low = Σ(value < threshold1)`, `n_very_low = Σ(value < q347)`,
  `pct_low = round(n_low / n_total * 100)` (0 if `n_total == 0`).
- Used once per canton (full region set) and once per region (single id).

### `src/models.py` — `RegionReport` new fields
- `discharge: DischargeStats` — per-region discharge stats.
- `precip_1m_index_forecast: int | None`, `soil_moisture_index_forecast: int | None`
  — week-2 p50 from `weekly_forecast_regions` (`precip_1m_index_p50`,
  `soil_moisture_index_p50`), same row selection as `_compute_cdi_forecast_week2`.
- `precip_deficit_delta: int`, `soil_moisture_deficit_delta: int`
  — `forecast_index − current_index`; `0` when forecast missing. Passed to the
  renderer `trend(delta, "defizit")` helper.

### `src/models.py` — `CantonReport` new fields
- `n_regions_dry: int` — regions with `cdi > 1`.
- `cdi_min_dry: int | None`, `cdi_max_dry: int | None` — min/max CDI among dry
  regions (`None` when none dry).
- `cdi_situation_delta: int` — `sum(forecast cdi) − sum(current cdi)`.
- `mean_precip_sum_1m: float`, `mean_precip_sum_3m: float` — mean over regions,
  rounded to 1 decimal.
- `precip_index_min: int`, `precip_index_max: int` — min/max `precip_1m_index`.
- `discharge: DischargeStats` — canton-wide.
- `n_regions_with_precip_deficit: int`, `n_regions_with_soil_moisture_deficit: int`
  — count of regions with the respective index ≥ 2 (replaces the inline
  `.get(2,0)+…` arithmetic in the YAML).

### `src/aggregation/regional.py`
- Add the forecast-index lookups (generalise the existing
  `_compute_cdi_forecast_week2` to a helper that takes a column name and returns
  the week-2 p50 value).
- Compute `precip_deficit_delta` / `soil_moisture_deficit_delta`.
- Call `compute_discharge_stats([region_id], bundle)` for the per-region
  `discharge` field.

### `src/aggregation/canton.py`
- Fold the new canton aggregates from the region reports + forecast.
- Call `compute_discharge_stats(region_ids, bundle)` once for the canton.

## Part 3 — Ruleset (YAML) & renderer

### `src/briefing/renderer.py`
- Extend `_handlebars_to_jinja2` to support `{{#if <expr>}} … {{/if}}`
  (translate to `{% if <expr> %} … {% endif %}`), keeping the YAML in one
  consistent mini-language. Used for the zero-stations phrase and the empty
  dry-range parenthetical.
- Add a `deficit_range(min_idx, max_idx, key)` global (mirrors the `trend()`
  global). Builds the localized range phrase from the nomenclature adjective
  maps:
  - `min_idx is None` → returns `""`.
  - `min_idx == max_idx` → single noun phrase (e.g. "ein grosses
    Niederschlagsdefizit").
  - else → "<noun-with-min-adjective> bis <max-adjective>" composition, e.g.
    "ein leichtes bis grosses Niederschlagsdefizit"; for `cdi` →
    "leicht trocken bis sehr trocken".
- Expose `banner` and `weiterführende_links` (canton-resolved) to the
  environment/`BriefingDocument` for `app.py` and the HTML export to render.

### `src/briefing/schemas.py`
Add Pydantic models for: `banner` (list of `{label, url}`),
`weiterführende_links` (canton-keyed link lists), `trend.situation`
(increase/decrease/stable with `{de, fr}`), and a `niederschlag.adjective`
sub-map.

### `data/ruleset/canton-bulletin.yaml`

**New `trend.situation`** (full predicate values for clean grammar):
- increase: `de: "wird sich voraussichtlich verschlechtern"`, `fr: …`
- decrease: `de: "wird sich voraussichtlich verbessern"`, `fr: …`
- stable:   `de: "wird voraussichtlich unverändert bleiben"`, `fr: …`

**`niederschlag.adjective`** (bare adjectives for range composition):
1: "kein/geringes", 2: "leichtes", 3: "erhebliches", 4: "grosses",
5: "extremes" (+ fr). `cdi.adjective` already exists and is reused.

**New `banner` block** (top, after title): Trockenheitsportal
(`https://www.trockenheit.admin.ch`), waldbrandgefahr.ch, Naturgefahrenportal.

**New `weiterführende_links` block** referenced inside `allgemeine-lage`:
- canton-keyed Grundwasser link (BE:
  `https://www.bvd.be.ch/de/start/themen/wasser/hydrologische-daten/regionale-grundwasserauswertung.html`)
- Vegetationszustand VHI
  (`https://www.trockenheit.admin.ch/de/faktoren/vegetation/vegetationszustand-vhi`)

**`allgemeine-lage`** rewritten (de; fr mirrored, flagged for review):
```
Im Kanton {{ canton.canton_name_de }} sind aktuell {{ canton.n_regions_dry }} von
{{ canton.regions|length }} Regionen trocken{{#if canton.cdi_min_dry}} ({{ deficit_range(canton.cdi_min_dry, canton.cdi_max_dry, "cdi") }}){{/if}}.
Die Situation {{ trend(canton.cdi_situation_delta, "situation") }}.

In den vergangenen 30 Tagen sind durchschnittlich rund {{ canton.mean_precip_sum_1m }} mm
Niederschlag gefallen (3-Monats-Summe: {{ canton.mean_precip_sum_3m }} mm). Im langjährigen
Vergleich bedeutet dies regional {{ deficit_range(canton.precip_index_min, canton.precip_index_max, "niederschlag") }}.

{{#if canton.discharge.n_total}}{{ canton.discharge.pct_low }} % der Abflussmessstationen im
Kanton weisen aktuell einen niedrigen Abfluss (7-Tages-Mittel) auf. Davon liegen
{{ canton.discharge.n_very_low }} Stationen im sehr niedrigen Bereich.{{/if}}{{#if not canton.discharge.n_total}}Im Kanton gibt es keine Abflussmessstationen.{{/if}}

Bei der Bodenfeuchte weisen {{ canton.n_regions_with_soil_moisture_deficit }} von
{{ canton.regions|length }} Warnregionen ein Defizit auf.
```
(+ the `weiterführende_links` list appended.)

**`regionen`** per-region body rewritten:
```
### {{ this.region_name_de }}

In den vergangenen 30 Tagen sind in der Region {{ this.region_name_de }} rund
{{ this.precip_sum_1m }} mm Niederschlag gefallen (3-Monats-Summe: {{ this.precip_sum_3m }} mm).
Die Region weist damit aktuell {{ nomenclature.niederschlag.noun[this.precip_1m_index].de }} auf.
Das Defizit wird in nächster Zeit tendenziell {{ trend(this.precip_deficit_delta, "defizit") }}.

{{#if this.discharge.n_total}}{{ this.discharge.pct_low }} % der Abflussmessstationen weisen
aktuell einen niedrigen Abfluss (7-Tages-Mittel) auf. Davon liegen {{ this.discharge.n_very_low }}
Stationen im sehr niedrigen Bereich.{{/if}}{{#if not this.discharge.n_total}}In dieser Region gibt es keine Abflussmessstationen.{{/if}}

Es besteht zurzeit {{ nomenclature.bodenfeuchte.noun[this.soil_moisture_index].de }}.
Das Defizit wird in nächster Zeit tendenziell {{ trend(this.soil_moisture_deficit_delta, "defizit") }}.
```

## App / export

`app.py` and `src/export/report.py` render the new `banner` link row (top) and
`weiterführende_links` (within / after Allgemeine Lage). No Streamlit imports
leak outside `app.py`.

## Testing

- `tests/test_stations.py`: `compute_discharge_stats` — low/very-low counting,
  doy join, leading-zero IDs, zero-station case, percentage rounding.
- `tests/test_aggregation.py`: new `CantonReport` fields (n_regions_dry, cdi
  min/max dry, situation delta sign, mean precip, precip index min/max, deficit
  counts) and `RegionReport` deficit deltas incl. missing-forecast → 0.
- `tests/test_fixture_loader.py`: station DataFrames + map populated; IDs are str.
- `tests/test_renderer.py` (or existing): `deficit_range` (None/equal/range,
  cdi vs niederschlag), `{{#if}}` translation, `trend.situation` rendering,
  full `allgemeine-lage` + `regionen` render against a fixture canton.
- Update `docs/index.html` stlite file list with `src/aggregation/stations.py`.

## Open / follow-up

- French strings for the new blocks are drafted by mirroring existing style and
  must be reviewed by the user (terminology consistency).
