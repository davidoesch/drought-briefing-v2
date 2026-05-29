# French Language Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add French (FR) as a fully localized second language alongside German (DE) — briefing text, UI labels, region names, CDI labels — switched by a sidebar toggle.

**Architecture:** Parallel text-block files per language (`text_blocks_de.py`, `text_blocks_fr.py`); a new `src/i18n/strings.py` module for all UI strings; `build_briefing(report, mode, lang="de")` selects blocks and trend labels by language; `app.py` reads `lang` from a sidebar radio and calls `t(key, lang)` everywhere.

**Tech Stack:** Python 3.12, Streamlit, uv (`uv run pytest` for tests, `uv run streamlit run app.py` to verify UI)

---

## File Map

| Action | Path | Purpose |
|--------|------|---------|
| Modify | `config/settings.py` | Add `BERNE_REGION_NAMES_FR`, `CDI_LABELS_FR` |
| Create | `src/i18n/__init__.py` | Package marker |
| Create | `src/i18n/strings.py` | `UI_STRINGS` dict + `t()`, `get_cdi_labels()`, `get_region_names()` |
| Rename | `src/briefing/text_blocks.py` → `src/briefing/text_blocks_de.py` | German text blocks (no content change) |
| Create | `src/briefing/text_blocks_fr.py` | French text blocks (same 4-dict structure) |
| Modify | `src/briefing/template.py` | `lang` param on `build_briefing`; restructured `_TREND_LABELS`; remove `translate()` stub |
| Modify | `app.py` | Language toggle; all strings via `t()`; `lang` passed to `build_briefing` |
| Modify | `docs/index.html` | Update stlite manifest (add 4 new files, remove old `text_blocks.py`) |
| Create | `tests/test_i18n.py` | Tests for `t()`, `get_cdi_labels()`, `get_region_names()`, FR settings dicts |
| Create | `tests/test_briefing_fr.py` | Tests for `build_briefing(..., lang="fr")` |

---

## Task 1: Add French dictionaries to settings

**Files:**
- Modify: `config/settings.py`
- Create: `tests/test_i18n.py` (initial stub)

- [ ] **Step 1: Create failing test**

Create `tests/test_i18n.py`:

```python
# tests/test_i18n.py
from config.settings import BERNE_REGION_NAMES_FR, CDI_LABELS_FR


def test_fr_region_names_has_all_berne_regions():
    from config.settings import BERNE_REGION_IDS
    assert set(BERNE_REGION_NAMES_FR.keys()) == BERNE_REGION_IDS


def test_fr_cdi_labels_has_all_levels():
    assert set(CDI_LABELS_FR.keys()) == set(range(6))


def test_fr_region_34_is_mittelland():
    assert BERNE_REGION_NAMES_FR[34] == "Mittelland bernois"


def test_fr_cdi_label_0_is_no_drought():
    assert CDI_LABELS_FR[0] == "Pas de sécheresse"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_i18n.py -v
```

Expected: `ImportError: cannot import name 'BERNE_REGION_NAMES_FR'`

- [ ] **Step 3: Add FR dicts to settings.py**

Open `config/settings.py`. After the `CDI_LABELS` dict (line 18–25), add:

```python
CDI_LABELS_FR: Final[dict[int, str]] = {
    0: "Pas de sécheresse",
    1: "Sécheresse légère",
    2: "Sécheresse notable",
    3: "Sécheresse sévère",
    4: "Sécheresse extrême",
    5: "Sécheresse exceptionnelle",
}
```

After `BERNE_REGION_NAMES` (line 9–16), add:

```python
BERNE_REGION_NAMES_FR: Final[dict[int, str]] = {
    33: "Basse-Emmental",
    34: "Mittelland bernois",
    35: "Oberland bernois occidental",
    37: "Haute-Argovie",
    38: "Haute-Emmental",
    41: "Oberland bernois oriental",
}
```

- [ ] **Step 4: Run test to verify it passes**

```bash
uv run pytest tests/test_i18n.py -v
```

Expected: 4 tests PASS

- [ ] **Step 5: Run all tests to confirm nothing broke**

```bash
uv run pytest tests/ -v
```

Expected: all existing tests PASS

- [ ] **Step 6: Commit**

```bash
git add config/settings.py tests/test_i18n.py
git commit -m "feat: add French region names and CDI labels to settings"
```

---

## Task 2: Create i18n module

**Files:**
- Create: `src/i18n/__init__.py`
- Create: `src/i18n/strings.py`
- Modify: `tests/test_i18n.py` (add strings tests)

- [ ] **Step 1: Add failing tests to test_i18n.py**

Append to `tests/test_i18n.py`:

```python
from src.i18n.strings import t, get_cdi_labels, get_region_names


def test_t_returns_german_for_de():
    assert t("section_lage", "de") == "Lage"


def test_t_returns_french_for_fr():
    assert t("section_lage", "fr") == "Situation"


def test_t_falls_back_for_unknown_lang():
    assert t("section_lage", "it") == "Lage"


def test_t_returns_key_for_unknown_key():
    assert t("__nonexistent__", "de") == "__nonexistent__"


def test_get_cdi_labels_de():
    labels = get_cdi_labels("de")
    assert labels[0] == "Keine Trockenheit"


def test_get_cdi_labels_fr():
    labels = get_cdi_labels("fr")
    assert labels[0] == "Pas de sécheresse"


def test_get_region_names_de():
    names = get_region_names("de")
    assert names[34] == "Berner Mittelland"


def test_get_region_names_fr():
    names = get_region_names("fr")
    assert names[34] == "Mittelland bernois"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_i18n.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.i18n'`

- [ ] **Step 3: Create package marker**

Create `src/i18n/__init__.py` as an empty file.

- [ ] **Step 4: Create strings.py**

Create `src/i18n/strings.py`:

```python
# src/i18n/strings.py
from __future__ import annotations

from config.settings import (
    BERNE_REGION_NAMES,
    BERNE_REGION_NAMES_FR,
    CDI_LABELS,
    CDI_LABELS_FR,
)

UI_STRINGS: dict[str, dict[str, str]] = {
    "de": {
        "lang_toggle_label": "Sprache / Langue",
        "app_title": "Trockenheitsbriefing Kanton Bern",
        "sidebar_title": "💧 Trockenheitsbriefing",
        "sidebar_caption": "Kanton Bern · trockenheit.admin.ch",
        "mode_label": "Ausgabemodus",
        "mode_behoerden": "⚖ Behördenbriefing",
        "mode_bulletin": "📰 Mein Trockenheitsbulletin",
        "region_label": "Warnregion (Kanton Bern)",
        "data_status": "🟢 Datenstand",
        "stand": "Stand",
        "source": "Quelle",
        "export_header": "Export",
        "briefing_title": "Trockenheit",
        "metric_spi": "SPI-3m",
        "metric_spi_help": "{percentile}. Perzentil (Ref. 1961–2020)",
        "metric_soil": "Bodenfeuchte (% nFK)",
        "metric_vhi": "VHI",
        "metric_critical": "% krit. Wochen",
        "metric_critical_help": "Anteil Wochen mit CDI ≥ 3 in den letzten 52 Wochen",
        "section_map": "CDI-Karte Kanton Bern",
        "section_chart": "Zeitreihe — letzte 52 Wochen",
        "section_lage": "Lage",
        "section_entwicklung": "Entwicklung",
        "section_einordnung": "Einordnung",
        "quality_expander": "Qualität & Datengrundlage",
        "data_age": "Aktualität",
        "coverage": "Abdeckung",
        "quality_missing_cols": "Fehlende Spalten",
        "quality_outliers": "Ausreisser-Warnung",
        "pdf_hint": "💡 PDF: Datei → Drucken → Als PDF speichern (Ctrl+P)",
        "btn_html": "⬇ HTML exportieren",
        "unknown": "Unbekannt",
    },
    "fr": {
        "lang_toggle_label": "Sprache / Langue",
        "app_title": "Bulletin de sécheresse — Canton de Berne",
        "sidebar_title": "💧 Bulletin de sécheresse",
        "sidebar_caption": "Canton de Berne · trockenheit.admin.ch",
        "mode_label": "Mode de sortie",
        "mode_behoerden": "⚖ Briefing autorités",
        "mode_bulletin": "📰 Mon bulletin sécheresse",
        "region_label": "Région d'avertissement (Canton de Berne)",
        "data_status": "🟢 État des données",
        "stand": "État",
        "source": "Source",
        "export_header": "Export",
        "briefing_title": "Sécheresse",
        "metric_spi": "SPI-3m",
        "metric_spi_help": "{percentile}e percentile (réf. 1961–2020)",
        "metric_soil": "Humidité du sol (% RFU)",
        "metric_vhi": "VHI",
        "metric_critical": "% semaines critiques",
        "metric_critical_help": "Part des semaines avec CDI ≥ 3 au cours des 52 dernières semaines",
        "section_map": "Carte CDI — Canton de Berne",
        "section_chart": "Série temporelle — 52 dernières semaines",
        "section_lage": "Situation",
        "section_entwicklung": "Évolution",
        "section_einordnung": "Contextualisation",
        "quality_expander": "Qualité & base de données",
        "data_age": "Actualité",
        "coverage": "Couverture",
        "quality_missing_cols": "Colonnes manquantes",
        "quality_outliers": "Avertissement valeurs aberrantes",
        "pdf_hint": "💡 PDF : Fichier → Imprimer → Enregistrer en PDF (Ctrl+P)",
        "btn_html": "⬇ Exporter HTML",
        "unknown": "Inconnu",
    },
}


def t(key: str, lang: str) -> str:
    """Return UI string for key in lang, falling back to German."""
    de = UI_STRINGS["de"]
    return UI_STRINGS.get(lang, de).get(key, de.get(key, key))


def get_cdi_labels(lang: str) -> dict[int, str]:
    return CDI_LABELS_FR if lang == "fr" else CDI_LABELS


def get_region_names(lang: str) -> dict[int, str]:
    return BERNE_REGION_NAMES_FR if lang == "fr" else BERNE_REGION_NAMES
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
uv run pytest tests/test_i18n.py -v
```

Expected: all tests PASS

- [ ] **Step 6: Run all tests**

```bash
uv run pytest tests/ -v
```

Expected: all existing tests PASS

- [ ] **Step 7: Commit**

```bash
git add src/i18n/__init__.py src/i18n/strings.py tests/test_i18n.py
git commit -m "feat: add i18n module with t(), get_cdi_labels(), get_region_names()"
```

---

## Task 3: Rename text_blocks.py → text_blocks_de.py

**Files:**
- Rename: `src/briefing/text_blocks.py` → `src/briefing/text_blocks_de.py`
- Modify: `src/briefing/template.py` (update import — must happen in same step to avoid breaking tests)

This task is a pure refactor — no new behavior, no new tests. The existing `tests/test_text_blocks.py` tests via `build_briefing()`, which in turn imports the blocks, so it validates the rename indirectly.

- [ ] **Step 1: Rename the file**

```bash
git mv src/briefing/text_blocks.py src/briefing/text_blocks_de.py
```

- [ ] **Step 2: Verify tests are currently broken (import error)**

```bash
uv run pytest tests/test_text_blocks.py -v 2>&1 | head -20
```

Expected: `ModuleNotFoundError: No module named 'src.briefing.text_blocks'`

- [ ] **Step 3: Update the import in template.py**

In `src/briefing/template.py`, replace:

```python
from config.settings import CDI_LABELS
from src.briefing.text_blocks import (
    DATENGRUNDLAGE_BLOCKS,
    ENTWICKLUNG_BLOCKS,
    EINORDNUNG_BLOCKS,
    LAGE_BLOCKS,
)
```

with:

```python
from src.briefing import text_blocks_de
```

Also remove the `translate()` stub at the bottom of the file (lines 65–67):

```python
def translate(text: str, lang: str = "de") -> str:
    """FR/IT translation stub — returns German text unchanged."""
    return text
```

And update `_format_kwargs` to use `text_blocks_de` references where needed. (Full template.py rewrite is in Task 5 — for now, just make the import work by keeping the same logic but using `text_blocks_de.LAGE_BLOCKS`, etc.)

Replace the body of `build_briefing`:

```python
def build_briefing(report: RegionReport, mode: str) -> BriefingDocument:
    cdi = min(max(report.cdi, 0), 5)
    fmt = _format_kwargs(report, mode)
    sections = {
        "lage":           text_blocks_de.LAGE_BLOCKS[mode][cdi].format(**fmt),
        "entwicklung":    text_blocks_de.ENTWICKLUNG_BLOCKS[mode][cdi].format(**fmt),
        "einordnung":     text_blocks_de.EINORDNUNG_BLOCKS[mode][cdi].format(**fmt),
        "datengrundlage": text_blocks_de.DATENGRUNDLAGE_BLOCKS[mode].format(**fmt),
    }
    return BriefingDocument(
        sections=sections,
        report=report,
        mode=mode,
        generated_at=datetime.now(),
    )
```

Also update `_format_kwargs` — replace `CDI_LABELS.get(...)` with a local import since `CDI_LABELS` is no longer imported at the top:

```python
def _format_kwargs(report: RegionReport, mode: str) -> dict:
    from config.settings import CDI_LABELS
    return {
        "region":            report.region_name_de,
        "cdi":               report.cdi,
        "cdi_label":         CDI_LABELS.get(report.cdi, "Unbekannt"),
        "spi_3m":            report.spi_3m,
        "spi_3m_delta":      report.spi_3m_delta,
        "soil_moisture_pct": report.soil_moisture_pct,
        "vhi":               _safe_num(report.vhi),
        "vhi_delta":         _safe_num(report.vhi_delta),
        "pct_critical_pct":  report.pct_critical * 100,
        "spi_3m_percentile": report.spi_3m_percentile,
        "data_timestamp":    report.data_timestamp.strftime("%d.%m.%Y"),
        "coverage_pct":      report.quality.coverage_pct,
        "overall":           report.quality.overall,
        "trend_de":          _TREND_LABELS.get(report.cdi_trend, {}).get(mode, "stabil"),
        "trend_de_bulletin": _TREND_LABELS.get(report.cdi_trend, {}).get("bulletin", "stabilisiert"),
    }
```

- [ ] **Step 4: Run all tests to verify they pass**

```bash
uv run pytest tests/ -v
```

Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/briefing/text_blocks_de.py src/briefing/template.py
git commit -m "refactor: rename text_blocks.py to text_blocks_de.py, update imports"
```

---

## Task 4: Create text_blocks_fr.py

**Files:**
- Create: `src/briefing/text_blocks_fr.py`
- Create: `tests/test_briefing_fr.py` (initial import test)

- [ ] **Step 1: Create failing test**

Create `tests/test_briefing_fr.py`:

```python
# tests/test_briefing_fr.py
from src.briefing.text_blocks_fr import (
    LAGE_BLOCKS,
    ENTWICKLUNG_BLOCKS,
    EINORDNUNG_BLOCKS,
    DATENGRUNDLAGE_BLOCKS,
)


def test_fr_lage_blocks_has_both_modes():
    assert "behoerden" in LAGE_BLOCKS
    assert "bulletin" in LAGE_BLOCKS


def test_fr_lage_blocks_has_all_cdi_levels():
    for mode in ("behoerden", "bulletin"):
        assert set(LAGE_BLOCKS[mode].keys()) == set(range(6))


def test_fr_entwicklung_blocks_has_both_modes():
    assert "behoerden" in ENTWICKLUNG_BLOCKS
    assert "bulletin" in ENTWICKLUNG_BLOCKS


def test_fr_einordnung_blocks_has_both_modes():
    assert "behoerden" in EINORDNUNG_BLOCKS
    assert "bulletin" in EINORDNUNG_BLOCKS


def test_fr_datengrundlage_blocks_has_both_modes():
    assert "behoerden" in DATENGRUNDLAGE_BLOCKS
    assert "bulletin" in DATENGRUNDLAGE_BLOCKS


def test_fr_blocks_contain_french_word():
    assert "sécheresse" in LAGE_BLOCKS["bulletin"][0].lower() or \
           "sécheresse" in LAGE_BLOCKS["bulletin"][1].lower()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
uv run pytest tests/test_briefing_fr.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.briefing.text_blocks_fr'`

- [ ] **Step 3: Create text_blocks_fr.py**

Create `src/briefing/text_blocks_fr.py` with this exact content:

```python
# src/briefing/text_blocks_fr.py
"""
French text blocks — same 4-dict structure as text_blocks_de.py.
Slots are identical: {region}, {cdi}, {cdi_label}, {spi_3m:.2f}, etc.
"""
from __future__ import annotations

LAGE_BLOCKS: dict[str, dict[int, str]] = {
    "behoerden": {
        0: "{region} : CDI {cdi} ({cdi_label}). SPI-3m {spi_3m:.2f}. Humidité du sol {soil_moisture_pct:.0f}% RFU. VHI {vhi:.1f}.",
        1: "{region} : CDI {cdi} ({cdi_label}). SPI-3m {spi_3m:.2f}. Humidité du sol {soil_moisture_pct:.0f}% RFU. VHI {vhi:.1f}.",
        2: "{region} : CDI {cdi} ({cdi_label}). SPI-3m {spi_3m:.2f} (sous le seuil -0.84). Humidité du sol {soil_moisture_pct:.0f}% RFU. VHI {vhi:.1f}.",
        3: "{region} : CDI {cdi} ({cdi_label}). SPI-3m {spi_3m:.2f}. Humidité du sol {soil_moisture_pct:.0f}% RFU. VHI {vhi:.1f}. Vigilance accrue requise.",
        4: "{region} : CDI {cdi} ({cdi_label}). SPI-3m {spi_3m:.2f}. Humidité du sol {soil_moisture_pct:.0f}% RFU. VHI {vhi:.1f}. Examiner les mesures immédiates.",
        5: "{region} : CDI {cdi} ({cdi_label}). SPI-3m {spi_3m:.2f}. Humidité du sol {soil_moisture_pct:.0f}% RFU. VHI {vhi:.1f}. Situation extraordinaire.",
    },
    "bulletin": {
        0: "Dans {region}, la situation de sécheresse est normale. L'indice combiné de sécheresse (CDI) est de {cdi} et n'indique aucune sécheresse. L'humidité du sol est de {soil_moisture_pct:.0f}% de la réserve facilement utilisable (RFU).",
        1: "Dans {region}, une légère sécheresse est observée (CDI {cdi}). Les précipitations des trois derniers mois, avec un SPI-3m de {spi_3m:.2f}, sont légèrement inférieures à la moyenne. L'humidité du sol est de {soil_moisture_pct:.0f}% RFU.",
        2: "Dans {region}, une sécheresse notable est constatée (CDI {cdi}). La valeur SPI-3m de {spi_3m:.2f} indique un déficit pluviométrique marqué. L'humidité du sol est de {soil_moisture_pct:.0f}% RFU.",
        3: "Dans {region}, une sécheresse sévère sévit (CDI {cdi}). La valeur SPI-3m de {spi_3m:.2f} indique un déficit pluviométrique important. L'humidité du sol n'est que de {soil_moisture_pct:.0f}% RFU. La situation nécessite une attention particulière.",
        4: "Dans {region}, une sécheresse extrême sévit (CDI {cdi}). La valeur SPI-3m de {spi_3m:.2f} et une humidité du sol de {soil_moisture_pct:.0f}% RFU indiquent une situation très grave. Des mesures pour limiter les dommages doivent être examinées.",
        5: "Dans {region}, une sécheresse exceptionnelle sévit (CDI {cdi}). Il s'agit d'une situation extrême très rare. Toutes les mesures disponibles doivent être examinées.",
    },
}

ENTWICKLUNG_BLOCKS: dict[str, dict[int, str]] = {
    "behoerden": {
        0: "Tendance : {trend_de}. Delta SPI-3m : {spi_3m_delta:+.2f}/semaine. Delta VHI : {vhi_delta:+.1f}.",
        1: "Tendance : {trend_de}. Delta SPI-3m : {spi_3m_delta:+.2f}/semaine. Delta VHI : {vhi_delta:+.1f}.",
        2: "Tendance : {trend_de}. Delta SPI-3m : {spi_3m_delta:+.2f}/semaine. Delta VHI : {vhi_delta:+.1f}.",
        3: "Tendance : {trend_de}. Delta SPI-3m : {spi_3m_delta:+.2f}/semaine. Delta VHI : {vhi_delta:+.1f}. Surveiller l'évolution.",
        4: "Tendance : {trend_de}. Delta SPI-3m : {spi_3m_delta:+.2f}/semaine. Delta VHI : {vhi_delta:+.1f}. Escalade possible.",
        5: "Tendance : {trend_de}. Delta SPI-3m : {spi_3m_delta:+.2f}/semaine. Delta VHI : {vhi_delta:+.1f}. Surveillance critique de la situation.",
    },
    "bulletin": {
        0: "La situation dans {region} est stable. Aucun changement significatif par rapport à la semaine précédente.",
        1: "La situation de sécheresse dans {region} {trend_de_bulletin}. La valeur SPI-3m a évolué de {spi_3m_delta:+.2f}.",
        2: "La situation de sécheresse dans {region} {trend_de_bulletin}. L'état de la végétation (VHI) a évolué de {vhi_delta:+.1f} points.",
        3: "La sécheresse sévère dans {region} {trend_de_bulletin}. Une attention particulière est requise pour l'agriculture et l'approvisionnement en eau.",
        4: "La sécheresse extrême dans {region} {trend_de_bulletin}. Le SPI-3m a évolué de {spi_3m_delta:+.2f}. Des mesures immédiates pourraient être nécessaires.",
        5: "La sécheresse exceptionnelle dans {region} persiste. Toutes les capacités d'intervention disponibles devraient être mobilisées.",
    },
}

EINORDNUNG_BLOCKS: dict[str, dict[int, str]] = {
    "behoerden": {
        0: "Contextualisation hist. : {pct_critical_pct:.0f}% semaines critiques (52 dern. sem.). SPI-3m au {spi_3m_percentile}e percentile (réf. 1961-2020). Aucune anomalie.",
        1: "Contextualisation hist. : {pct_critical_pct:.0f}% semaines critiques (52 dern. sem.). SPI-3m au {spi_3m_percentile}e percentile (réf. 1961-2020).",
        2: "Contextualisation hist. : {pct_critical_pct:.0f}% semaines critiques (52 dern. sem.). SPI-3m au {spi_3m_percentile}e percentile (réf. 1961-2020). Sous la médiane.",
        3: "Contextualisation hist. : {pct_critical_pct:.0f}% semaines critiques (52 dern. sem.). SPI-3m au {spi_3m_percentile}e percentile (réf. 1961-2020). Situation rare.",
        4: "Contextualisation hist. : {pct_critical_pct:.0f}% semaines critiques (52 dern. sem.). SPI-3m au {spi_3m_percentile}e percentile (réf. 1961-2020). Situation extrême très rare.",
        5: "Contextualisation hist. : {pct_critical_pct:.0f}% semaines critiques (52 dern. sem.). SPI-3m au {spi_3m_percentile}e percentile (réf. 1961-2020). Exceptionnellement rare.",
    },
    "bulletin": {
        0: "Par rapport à la moyenne à long terme (1961-2020), la situation actuelle dans {region} est normale. Au cours des 52 dernières semaines, il y a eu {pct_critical_pct:.0f}% de semaines avec une sécheresse critique (CDI >= 3).",
        1: "La valeur SPI-3m se situe au {spi_3m_percentile}e percentile de la période de référence 1961-2020. Au cours des 52 dernières semaines, {pct_critical_pct:.0f}% des semaines étaient critiques.",
        2: "La valeur SPI-3m actuelle se situe au {spi_3m_percentile}e percentile de la période de référence 1961-2020. Au cours des 52 dernières semaines, {pct_critical_pct:.0f}% étaient critiques.",
        3: "La valeur SPI-3m se situe au {spi_3m_percentile}e percentile de la période de référence — une situation rare. Au cours des 52 dernières semaines, il y a eu {pct_critical_pct:.0f}% de semaines critiques.",
        4: "La valeur SPI-3m se situe au {spi_3m_percentile}e percentile de la période de référence — une situation extrême très rare. {pct_critical_pct:.0f}% des 52 dernières semaines étaient critiques.",
        5: "La valeur SPI-3m se situe au {spi_3m_percentile}e percentile de la période de référence — exceptionnellement rare. Dans {pct_critical_pct:.0f}% des 52 dernières semaines, une sécheresse critique régnait.",
    },
}

DATENGRUNDLAGE_BLOCKS: dict[str, str] = {
    "behoerden": (
        "Source : OFEV trockenheit.admin.ch. État des données : {data_timestamp}. "
        "Couverture : {coverage_pct:.0%}. Qualité des données : {overall}. "
        "Incertitudes : les valeurs sont basées sur des calculs de modèles ; des écarts locaux sont possibles."
    ),
    "bulletin": (
        "Les données proviennent de l'Office fédéral de l'environnement (OFEV), "
        "source : trockenheit.admin.ch. État : {data_timestamp}. "
        "Couverture des données : {coverage_pct:.0%}. "
        "Les valeurs sont basées sur des mesures et des calculs de modèles ; des écarts locaux sont possibles."
    ),
}
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
uv run pytest tests/test_briefing_fr.py -v
```

Expected: all tests PASS

- [ ] **Step 5: Run all tests**

```bash
uv run pytest tests/ -v
```

Expected: all tests PASS

- [ ] **Step 6: Commit**

```bash
git add src/briefing/text_blocks_fr.py tests/test_briefing_fr.py
git commit -m "feat: add French text blocks for all 4 briefing sections"
```

---

## Task 5: Update template.py with lang parameter

**Files:**
- Modify: `src/briefing/template.py` (full rewrite)
- Modify: `tests/test_briefing_fr.py` (add integration tests)

- [ ] **Step 1: Add failing integration tests to test_briefing_fr.py**

Append to `tests/test_briefing_fr.py`:

```python
import pytest
from datetime import datetime
from src.models import QualityReport, RegionReport
from src.briefing.template import build_briefing


@pytest.fixture
def sample_report():
    quality = QualityReport(
        data_age_days=1, coverage_pct=1.0,
        missing_columns=[], outlier_flags=[],
        is_stale=False, overall="ok",
    )
    return RegionReport(
        region_id=34, region_name_de="Berner Mittelland",
        data_timestamp=datetime(2026, 5, 26), source="fixture",
        cdi=2, spi_3m=-1.04, soil_moisture_pct=98.1, vhi=44.33,
        cdi_trend=0, spi_3m_delta=-0.05, vhi_delta=0.5,
        pct_critical=0.12, spi_3m_percentile=22, quality=quality,
    )


def test_build_briefing_fr_returns_french_lage(sample_report):
    doc = build_briefing(sample_report, "behoerden", lang="fr")
    assert "Humidité du sol" in doc.sections["lage"]
    assert "Bodenfeuchte" not in doc.sections["lage"]


def test_build_briefing_fr_returns_french_bulletin(sample_report):
    doc = build_briefing(sample_report, "bulletin", lang="fr")
    assert "sécheresse" in doc.sections["lage"].lower()


def test_build_briefing_fr_uses_french_region_name(sample_report):
    doc = build_briefing(sample_report, "behoerden", lang="fr")
    assert "Mittelland bernois" in doc.sections["lage"]
    assert "Berner Mittelland" not in doc.sections["lage"]


def test_build_briefing_de_default_unchanged(sample_report):
    doc = build_briefing(sample_report, "behoerden")
    assert "Bodenfeuchte" in doc.sections["lage"]


def test_build_briefing_fr_trend_label(sample_report):
    sample_report.cdi_trend = 0
    doc = build_briefing(sample_report, "behoerden", lang="fr")
    assert "stable" in doc.sections["entwicklung"]


@pytest.mark.parametrize("mode", ["behoerden", "bulletin"])
@pytest.mark.parametrize("cdi", range(6))
def test_fr_no_unfilled_slots(sample_report, mode, cdi):
    sample_report.cdi = cdi
    doc = build_briefing(sample_report, mode, lang="fr")
    for section_name, text in doc.sections.items():
        assert "{" not in text and "}" not in text, (
            f"Unfilled slot in {section_name} (mode={mode}, cdi={cdi}, lang=fr): {text}"
        )
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
uv run pytest tests/test_briefing_fr.py::test_build_briefing_fr_returns_french_lage -v
```

Expected: `TypeError: build_briefing() got an unexpected keyword argument 'lang'`

- [ ] **Step 3: Rewrite template.py**

Replace the entire content of `src/briefing/template.py`:

```python
# src/briefing/template.py
from __future__ import annotations

import math
from datetime import datetime

from src.briefing import text_blocks_de, text_blocks_fr
from src.i18n.strings import get_cdi_labels, get_region_names
from src.models import BriefingDocument, RegionReport

_BLOCKS_BY_LANG = {
    "de": text_blocks_de,
    "fr": text_blocks_fr,
}

_TREND_LABELS: dict[int, dict[str, dict[str, str]]] = {
    -1: {
        "de": {"behoerden": "verbessernd",     "bulletin": "verbessert"},
        "fr": {"behoerden": "s'améliorant",    "bulletin": "s'est améliorée"},
    },
    0: {
        "de": {"behoerden": "stabil",          "bulletin": "stabilisiert"},
        "fr": {"behoerden": "stable",          "bulletin": "s'est stabilisée"},
    },
    1: {
        "de": {"behoerden": "verschlechternd", "bulletin": "verschlechtert"},
        "fr": {"behoerden": "se dégradant",    "bulletin": "s'est dégradée"},
    },
}


def _safe_num(val: float, default: float = 0.0) -> float:
    return val if not math.isnan(val) else default


def _format_kwargs(report: RegionReport, mode: str, lang: str = "de") -> dict:
    trend_entry = _TREND_LABELS.get(report.cdi_trend, _TREND_LABELS[0])
    lang_trends = trend_entry.get(lang, trend_entry["de"])
    return {
        "region":            get_region_names(lang).get(report.region_id, report.region_name_de),
        "cdi":               report.cdi,
        "cdi_label":         get_cdi_labels(lang).get(report.cdi, ""),
        "spi_3m":            report.spi_3m,
        "spi_3m_delta":      report.spi_3m_delta,
        "soil_moisture_pct": report.soil_moisture_pct,
        "vhi":               _safe_num(report.vhi),
        "vhi_delta":         _safe_num(report.vhi_delta),
        "pct_critical_pct":  report.pct_critical * 100,
        "spi_3m_percentile": report.spi_3m_percentile,
        "data_timestamp":    report.data_timestamp.strftime("%d.%m.%Y"),
        "coverage_pct":      report.quality.coverage_pct,
        "overall":           report.quality.overall,
        "trend_de":          lang_trends.get(mode, lang_trends["behoerden"]),
        "trend_de_bulletin": lang_trends["bulletin"],
    }


def build_briefing(report: RegionReport, mode: str, lang: str = "de") -> BriefingDocument:
    blocks = _BLOCKS_BY_LANG.get(lang, text_blocks_de)
    cdi = min(max(report.cdi, 0), 5)
    fmt = _format_kwargs(report, mode, lang)
    sections = {
        "lage":           blocks.LAGE_BLOCKS[mode][cdi].format(**fmt),
        "entwicklung":    blocks.ENTWICKLUNG_BLOCKS[mode][cdi].format(**fmt),
        "einordnung":     blocks.EINORDNUNG_BLOCKS[mode][cdi].format(**fmt),
        "datengrundlage": blocks.DATENGRUNDLAGE_BLOCKS[mode].format(**fmt),
    }
    return BriefingDocument(
        sections=sections,
        report=report,
        mode=mode,
        generated_at=datetime.now(),
    )
```

- [ ] **Step 4: Run new tests to verify they pass**

```bash
uv run pytest tests/test_briefing_fr.py -v
```

Expected: all tests PASS

- [ ] **Step 5: Run all tests**

```bash
uv run pytest tests/ -v
```

Expected: all tests PASS (existing `test_text_blocks.py` tests still pass because `build_briefing(report, mode)` default `lang="de"` is backward-compatible)

- [ ] **Step 6: Commit**

```bash
git add src/briefing/template.py tests/test_briefing_fr.py
git commit -m "feat: add lang parameter to build_briefing, restructure _TREND_LABELS for DE/FR"
```

---

## Task 6: Update app.py with language toggle

**Files:**
- Modify: `app.py` (full rewrite)

No new unit tests — this is the UI layer. The existing test suite remains the correctness gate.

- [ ] **Step 1: Replace app.py**

Replace the entire content of `app.py`:

```python
# app.py
"""One Click Drought Briefing — Streamlit entry point for Kanton Bern."""
from __future__ import annotations

import logging
import math
import streamlit as st

from config.settings import BERNE_REGION_IDS, CDI_COLOURS
from src.aggregation.regional import compute_region_report
from src.briefing.template import build_briefing
from src.data.stac_client import load as load_data
from src.export.report import to_html
from src.i18n.strings import get_cdi_labels, get_region_names, t
from src.models import DataBundle
from src.viz.charts import build_timeseries
from src.viz.maps import build_export_map, build_map

st.set_page_config(
    page_title="Trockenheitsbriefing / Bulletin sécheresse",
    page_icon="💧",
    layout="wide",
)


@st.cache_data(ttl=3600, show_spinner="Daten werden geladen…")
def _load_bundle() -> DataBundle:
    return load_data()


# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("💧 Trockenheitsbriefing")
    st.caption("Kanton Bern · trockenheit.admin.ch")
    st.divider()

    lang = st.radio(
        "Sprache / Langue",
        options=["de", "fr"],
        format_func=lambda l: "Deutsch" if l == "de" else "Français",
        horizontal=True,
        index=0,
    )

    mode = st.radio(
        t("mode_label", lang),
        options=["behoerden", "bulletin"],
        format_func=lambda m: t("mode_behoerden", lang) if m == "behoerden" else t("mode_bulletin", lang),
        index=0,
    )

    region_options = sorted(BERNE_REGION_IDS)
    selected_region_id = st.selectbox(
        t("region_label", lang),
        options=region_options,
        format_func=lambda rid: get_region_names(lang).get(rid, str(rid)),
        index=1,
    )

    st.divider()

    bundle = _load_bundle()
    st.caption(f"{t('data_status', lang)}: {bundle.data_timestamp.strftime('%d.%m.%Y')}")
    st.caption(f"{t('source', lang)}: {bundle.source}")

    st.divider()
    st.subheader(t("export_header", lang))
    export_placeholder = st.empty()


# ── Pipeline ───────────────────────────────────────────────────────────────
all_reports = [compute_region_report(rid, bundle) for rid in BERNE_REGION_IDS]
report = next(r for r in all_reports if r.region_id == selected_region_id)
doc = build_briefing(report, mode, lang=lang)

mode_label = t("mode_behoerden", lang) if mode == "behoerden" else t("mode_bulletin", lang)

# ── Header ─────────────────────────────────────────────────────────────────
cdi_colour = CDI_COLOURS.get(report.cdi, "#cccccc")
cdi_label = get_cdi_labels(lang).get(report.cdi, t("unknown", lang))

col_title, col_badge = st.columns([4, 1])
with col_title:
    st.title(f"{mode_label}: {t('briefing_title', lang)}")
    st.caption(
        f"**{get_region_names(lang).get(report.region_id, report.region_name_de)}** · Kanton Bern · "
        f"{t('stand', lang)}: {report.data_timestamp.strftime('%d.%m.%Y')} · "
        f"{t('source', lang)}: {report.source}"
    )
with col_badge:
    st.markdown(
        f"""<div style="background:{cdi_colour};border-radius:10px;padding:12px;text-align:center;">
        <div style="font-size:11px;color:rgba(255,255,255,0.8);">CDI</div>
        <div style="font-size:36px;font-weight:bold;color:white;">{report.cdi}</div>
        <div style="font-size:11px;color:rgba(255,255,255,0.9);">{cdi_label}</div>
        </div>""",
        unsafe_allow_html=True,
    )

st.divider()

# ── Indicators ─────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric(t("metric_spi", lang), f"{report.spi_3m:.2f}", delta=f"{report.spi_3m_delta:+.2f}/Wo")
with c2:
    st.metric(
        t("metric_soil", lang),
        f"{report.soil_moisture_pct:.0f}%",
        help=t("metric_spi_help", lang).format(percentile=report.spi_3m_percentile),
    )
with c3:
    vhi_val = f"{report.vhi:.1f}" if not math.isnan(report.vhi) else "–"
    vhi_delta_str = f"{report.vhi_delta:+.1f}" if not math.isnan(report.vhi_delta) else None
    st.metric(t("metric_vhi", lang), vhi_val, delta=vhi_delta_str)
with c4:
    st.metric(
        t("metric_critical", lang),
        f"{report.pct_critical * 100:.0f}%",
        help=t("metric_critical_help", lang),
    )

# ── Map + Chart ────────────────────────────────────────────────────────────
map_col, chart_col = st.columns(2)

with map_col:
    st.subheader(t("section_map", lang))
    folium_map = build_map(report, all_reports)
    st.components.v1.html(folium_map._repr_html_(), height=300)

with chart_col:
    st.subheader(t("section_chart", lang))
    fig = build_timeseries(bundle.historic_df, selected_region_id)
    st.plotly_chart(fig, use_container_width=True)

# ── Text sections ──────────────────────────────────────────────────────────
st.divider()
for section_key in ["lage", "entwicklung", "einordnung"]:
    st.markdown(f"**{t('section_' + section_key, lang)}**")
    st.markdown(doc.sections[section_key])
    st.write("")

# ── Quality panel ──────────────────────────────────────────────────────────
with st.expander(t("quality_expander", lang)):
    q = report.quality
    q_colour = {"ok": "🟢", "warning": "🟡", "error": "🔴"}.get(q.overall, "⚪")
    st.markdown(
        f"{q_colour} **{q.overall.upper()}** — "
        f"{t('data_age', lang)}: {q.data_age_days} Tage — "
        f"{t('coverage', lang)}: {q.coverage_pct:.0%}"
    )
    if q.missing_columns:
        st.warning(f"{t('quality_missing_cols', lang)}: {', '.join(q.missing_columns)}")
    if q.outlier_flags:
        st.warning(f"{t('quality_outliers', lang)}: {', '.join(q.outlier_flags)}")
    st.caption(doc.sections["datengrundlage"])

# ── Export buttons ─────────────────────────────────────────────────────────
with export_placeholder:
    try:
        map_png = build_export_map(report, all_reports)
    except Exception as _exc:
        logging.warning("build_export_map failed (%r); HTML export will omit map", _exc)
        map_png = None
    html_str = to_html(doc, report, chart_fig=fig, map_png=map_png)

    st.info(t("pdf_hint", lang))
    st.download_button(
        label=t("btn_html", lang),
        data=html_str.encode("utf-8"),
        file_name=f"trockenheit_{report.region_name_de.replace(' ', '_')}_{report.data_timestamp.strftime('%Y%m%d')}.html",
        mime="text/html",
    )
```

- [ ] **Step 2: Run all tests**

```bash
uv run pytest tests/ -v
```

Expected: all tests PASS

- [ ] **Step 3: Commit**

```bash
git add app.py
git commit -m "feat: add DE/FR language toggle to sidebar, localize all UI strings"
```

---

## Task 7: Update stlite manifest

**Files:**
- Modify: `docs/index.html`

- [ ] **Step 1: Update the files block in docs/index.html**

In `docs/index.html`, replace the `files:` block inside the `stlite.mount(...)` call. The current block starts with `"app.py"` on line 27. Replace the entire `files: { ... }` object:

```javascript
files: {
  "app.py":                              { url: "./app.py" },
  "config/__init__.py":                  { url: "./config/__init__.py" },
  "config/settings.py":                  { url: "./config/settings.py" },
  "src/__init__.py":                     { url: "./src/__init__.py" },
  "src/models.py":                       { url: "./src/models.py" },
  "src/aggregation/__init__.py":         { url: "./src/aggregation/__init__.py" },
  "src/aggregation/indicators.py":       { url: "./src/aggregation/indicators.py" },
  "src/aggregation/regional.py":         { url: "./src/aggregation/regional.py" },
  "src/briefing/__init__.py":            { url: "./src/briefing/__init__.py" },
  "src/briefing/template.py":            { url: "./src/briefing/template.py" },
  "src/briefing/text_blocks_de.py":      { url: "./src/briefing/text_blocks_de.py" },
  "src/briefing/text_blocks_fr.py":      { url: "./src/briefing/text_blocks_fr.py" },
  "src/i18n/__init__.py":                { url: "./src/i18n/__init__.py" },
  "src/i18n/strings.py":                 { url: "./src/i18n/strings.py" },
  "src/data/__init__.py":                { url: "./src/data/__init__.py" },
  "src/data/fixture_loader.py":          { url: "./src/data/fixture_loader.py" },
  "src/data/stac_client.py":             { url: "./src/data/stac_client.py" },
  "src/export/__init__.py":              { url: "./src/export/__init__.py" },
  "src/export/report.py":               { url: "./src/export/report.py" },
  "src/quality/__init__.py":             { url: "./src/quality/__init__.py" },
  "src/quality/checks.py":              { url: "./src/quality/checks.py" },
  "src/viz/__init__.py":                 { url: "./src/viz/__init__.py" },
  "src/viz/charts.py":                   { url: "./src/viz/charts.py" },
  "src/viz/maps.py":                     { url: "./src/viz/maps.py" },
  "data/berne_warnregionen.geojson":
    { url: "./data/berne_warnregionen.geojson" },
  "data/trockenheitsdaten-numerisch_current__trockenheitsdaten-numerisch_current.csv.zip":
    { url: "./data/trockenheitsdaten-numerisch_current__trockenheitsdaten-numerisch_current.csv.zip" },
  "data/trockenheitsdaten-numerisch_historic__trockenheitsdaten-numerisch_historic.csv.zip":
    { url: "./data/trockenheitsdaten-numerisch_historic__trockenheitsdaten-numerisch_historic.csv.zip" },
  "data/trockenheitsdaten-numerisch_reference__trockenheitsdaten-numerisch_reference.csv.zip":
    { url: "./data/trockenheitsdaten-numerisch_reference__trockenheitsdaten-numerisch_reference.csv.zip" },
},
```

Key changes from old manifest:
- **Removed:** `"src/briefing/text_blocks.py"`
- **Added:** `"src/briefing/text_blocks_de.py"`, `"src/briefing/text_blocks_fr.py"`, `"src/i18n/__init__.py"`, `"src/i18n/strings.py"`

- [ ] **Step 2: Run all tests**

```bash
uv run pytest tests/ -v
```

Expected: all tests PASS

- [ ] **Step 3: Commit**

```bash
git add docs/index.html
git commit -m "chore: update stlite manifest for French language support (rename text_blocks, add i18n)"
```

---

## Verification

After all tasks complete, run the full test suite:

```bash
uv run pytest tests/ -v
```

Expected output summary: all tests pass, including the new FR tests.

To verify the UI manually:

```bash
uv run streamlit run app.py
```

- Confirm the language toggle (Deutsch / Français) appears at the top of the sidebar
- Switch to Français — verify all labels, metric names, section headings, and briefing text switch to French
- Switch back to Deutsch — verify German content is restored
- Test both modes (Behördenbriefing / Bulletin de sécheresse) in both languages
- Confirm HTML export button changes label between languages
