# French Language Support — Design Spec

**Date:** 2026-05-28
**Scope:** Full bilingual app (DE + FR), sidebar toggle, extensible to IT

---

## Goal

Add French as a second language to the Drought Briefing app. Every user-facing string — briefing text body, UI chrome, metric labels, section headings, CDI labels, region names — switches to French when the user selects FR in a sidebar toggle. German remains the default.

---

## Architecture

**Four layers of text are localized:**

1. **Briefing text blocks** (`src/briefing/`) — the generated Lage/Entwicklung/Einordnung/Datengrundlage paragraphs
2. **UI strings** (`src/i18n/strings.py`) — sidebar labels, metric names, headings, buttons, CDI labels
3. **Region names** (`config/settings.py`) — French names for the 6 Bern Warnregionen
4. **CDI labels** (`config/settings.py`) — French severity labels for CDI levels 0–5

Language is selected via a `st.radio` in the sidebar (before the mode radio), stored in session state. The `lang` value (`"de"` or `"fr"`) flows as a parameter through `build_briefing()` and `t()`.

---

## File Changes

### New files
- `src/briefing/text_blocks_de.py` — renamed from `text_blocks.py` (content unchanged)
- `src/briefing/text_blocks_fr.py` — same 4-dict structure as DE, French translations
- `src/i18n/__init__.py` — empty
- `src/i18n/strings.py` — `UI_STRINGS` dict + `t()`, `get_cdi_labels()`, `get_region_names()` helpers

### Modified files
- `src/briefing/template.py` — `build_briefing(report, mode, lang="de")` gains `lang` param; imports both text_blocks modules; `_TREND_LABELS` gains `fr` entries; remove `translate()` stub
- `config/settings.py` — add `BERNE_REGION_NAMES_FR`, `CDI_LABELS_FR`
- `app.py` — language toggle in sidebar; all string literals replaced with `t(key, lang)`; `build_briefing` called with `lang`
- `docs/index.html` — stlite file manifest updated (add `text_blocks_de.py`, `text_blocks_fr.py`, i18n files; remove old `text_blocks.py` entry)

---

## Section 1: Briefing layer

### `src/briefing/text_blocks_de.py`

Exact rename of `src/briefing/text_blocks.py`. No content change. All existing imports updated.

### `src/briefing/text_blocks_fr.py`

Same dict structure as the DE file:

```python
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
        2: "Dans {region}, une sécheresse modérée est constatée (CDI {cdi}). La valeur SPI-3m de {spi_3m:.2f} indique un déficit pluviométrique marqué. L'humidité du sol est de {soil_moisture_pct:.0f}% RFU.",
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
        "Les données proviennent de l'Office fédéral de l'environnement (OFEV), source : trockenheit.admin.ch. "
        "État : {data_timestamp}. Couverture des données : {coverage_pct:.0%}. "
        "Les valeurs sont basées sur des mesures et des calculs de modèles ; des écarts locaux sont possibles."
    ),
}
```

### `src/briefing/template.py` changes

`_TREND_LABELS` is restructured to support both languages:

```python
_TREND_LABELS: dict[int, dict[str, dict[str, str]]] = {
    -1: {
        "de": {"behoerden": "verbessernd", "bulletin": "verbessert"},
        "fr": {"behoerden": "s'améliorant", "bulletin": "s'est améliorée"},
    },
    0: {
        "de": {"behoerden": "stabil", "bulletin": "stabilisiert"},
        "fr": {"behoerden": "stable", "bulletin": "s'est stabilisée"},
    },
    1: {
        "de": {"behoerden": "verschlechternd", "bulletin": "verschlechtert"},
        "fr": {"behoerden": "se dégradant", "bulletin": "s'est dégradée"},
    },
}
```

`build_briefing(report, mode, lang="de")` signature and logic:

```python
def build_briefing(report: RegionReport, mode: str, lang: str = "de") -> BriefingDocument:
    from src.briefing import text_blocks_de, text_blocks_fr
    blocks = text_blocks_fr if lang == "fr" else text_blocks_de

    cdi = min(max(report.cdi, 0), 5)
    fmt = _format_kwargs(report, mode, lang)
    sections = {
        "lage":           blocks.LAGE_BLOCKS[mode][cdi].format(**fmt),
        "entwicklung":    blocks.ENTWICKLUNG_BLOCKS[mode][cdi].format(**fmt),
        "einordnung":     blocks.EINORDNUNG_BLOCKS[mode][cdi].format(**fmt),
        "datengrundlage": blocks.DATENGRUNDLAGE_BLOCKS[mode].format(**fmt),
    }
    return BriefingDocument(sections=sections, report=report, mode=mode, generated_at=datetime.now())
```

`_format_kwargs(report, mode, lang)` uses `BERNE_REGION_NAMES_FR` when lang="fr" and the lang-specific trend label:

```python
def _format_kwargs(report: RegionReport, mode: str, lang: str = "de") -> dict:
    from config.settings import BERNE_REGION_NAMES_FR
    trend_entry = _TREND_LABELS.get(report.cdi_trend, _TREND_LABELS[0])
    lang_trends = trend_entry.get(lang, trend_entry["de"])
    region_names_fr = BERNE_REGION_NAMES_FR if lang == "fr" else {}
    return {
        "region": region_names_fr.get(report.region_id, report.region_name_de),
        "cdi": report.cdi,
        "cdi_label": get_cdi_labels(lang).get(report.cdi, ""),
        "spi_3m": report.spi_3m,
        "spi_3m_delta": report.spi_3m_delta,
        "soil_moisture_pct": report.soil_moisture_pct,
        "vhi": _safe_num(report.vhi),
        "vhi_delta": _safe_num(report.vhi_delta),
        "pct_critical_pct": report.pct_critical * 100,
        "spi_3m_percentile": report.spi_3m_percentile,
        "data_timestamp": report.data_timestamp.strftime("%d.%m.%Y"),
        "coverage_pct": report.quality.coverage_pct,
        "overall": report.quality.overall,
        "trend_de": lang_trends[mode if mode in lang_trends else "behoerden"],
        "trend_de_bulletin": lang_trends["bulletin"],
    }
```

The existing `translate()` stub is removed.

---

## Section 2: i18n layer

### `config/settings.py` additions

```python
BERNE_REGION_NAMES_FR: Final[dict[int, str]] = {
    33: "Basse-Emmental",
    34: "Mittelland bernois",
    35: "Oberland bernois occidental",
    37: "Haute-Argovie",
    38: "Haute-Emmental",
    41: "Oberland bernois oriental",
}

CDI_LABELS_FR: Final[dict[int, str]] = {
    0: "Pas de sécheresse",
    1: "Sécheresse légère",
    2: "Sécheresse notable",
    3: "Sécheresse sévère",
    4: "Sécheresse extrême",
    5: "Sécheresse exceptionnelle",
}
```

### `src/i18n/strings.py`

```python
from __future__ import annotations
from config.settings import CDI_LABELS, CDI_LABELS_FR, BERNE_REGION_NAMES, BERNE_REGION_NAMES_FR

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
        "source": "Quelle",
        "export_header": "Export",
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
        "quality_missing_cols": "Fehlende Spalten",
        "quality_outliers": "Ausreisser-Warnung",
        "btn_html": "⬇ HTML exportieren",
        "pdf_hint": "💡 PDF: Datei → Drucken → Als PDF speichern (Ctrl+P)",
        "unknown": "Unbekannt",
        "data_age": "Aktualität",
        "coverage": "Abdeckung",
        "briefing_title": "Trockenheit",
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
        "source": "Source",
        "export_header": "Export",
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
        "quality_missing_cols": "Colonnes manquantes",
        "quality_outliers": "Avertissement valeurs aberrantes",
        "btn_html": "⬇ Exporter HTML",
        "pdf_hint": "💡 PDF : Fichier → Imprimer → Enregistrer en PDF (Ctrl+P)",
        "unknown": "Inconnu",
        "data_age": "Actualité",
        "coverage": "Couverture",
        "briefing_title": "Sécheresse",
    },
}


def t(key: str, lang: str) -> str:
    """Return UI string for key in lang, falling back to German."""
    return UI_STRINGS.get(lang, UI_STRINGS["de"]).get(key, UI_STRINGS["de"].get(key, key))


def get_cdi_labels(lang: str) -> dict[int, str]:
    return CDI_LABELS_FR if lang == "fr" else CDI_LABELS


def get_region_names(lang: str) -> dict[int, str]:
    return BERNE_REGION_NAMES_FR if lang == "fr" else BERNE_REGION_NAMES
```

---

## Section 3: `app.py` changes

Language toggle added to sidebar (before mode radio):

```python
lang = st.radio(
    t("lang_toggle_label", "de"),
    options=["de", "fr"],
    format_func=lambda l: "Deutsch" if l == "de" else "Français",
    horizontal=True,
)
```

All string literals replaced with `t(key, lang)` calls. Key changes:
- `st.set_page_config(page_title=t("app_title", lang))` — note: this runs before lang is known; use a default or skip localization of the page title
- Mode radio format_func: `lambda m: t("mode_behoerden", lang) if m == "behoerden" else t("mode_bulletin", lang)`
- Region selector format_func: `lambda rid: get_region_names(lang).get(rid, str(rid))`
- CDI badge: `cdi_label = get_cdi_labels(lang).get(report.cdi, t("unknown", lang))`
- `build_briefing(report, mode, lang=lang)`

> **Note on `st.set_page_config`:** This must be the first Streamlit call and runs before sidebar widgets are rendered. The page title cannot be dynamically localized per-session. It will remain in German as the browser tab title; the visible in-app title is fully localized.

---

## Section 4: stlite manifest (`docs/index.html`)

Remove entry for `src/briefing/text_blocks.py`. Add:
- `"src/briefing/text_blocks_de.py": { url: "./src/briefing/text_blocks_de.py" }`
- `"src/briefing/text_blocks_fr.py": { url: "./src/briefing/text_blocks_fr.py" }`
- `"src/i18n/__init__.py": { url: "./src/i18n/__init__.py" }`
- `"src/i18n/strings.py": { url: "./src/i18n/strings.py" }`

Total file count goes from 26 to 29. The GitHub Actions workflow uses `cp -r src _site/src` so it copies all new files without any workflow changes.

---

## Testing

- `tests/test_briefing_fr.py` — new test file:
  - `test_build_briefing_fr_lage()` — calls `build_briefing(report, "behoerden", lang="fr")`, asserts result contains French text (e.g., "CDI" and no "Bodenfeuchte")
  - `test_build_briefing_fr_bulletin()` — same for "bulletin" mode
  - `test_build_briefing_de_default()` — `build_briefing(report, "behoerden")` still returns German (backward-compatible default)
  - `test_trend_labels_fr()` — verifies `_format_kwargs` returns French trend words for lang="fr"

- `tests/test_i18n.py` — new test file:
  - `test_t_returns_french()` — `t("section_lage", "fr") == "Situation"`
  - `test_t_falls_back_to_german()` — `t("nonexistent_key", "fr")` returns the key (no crash)
  - `test_get_cdi_labels_fr()` — returns French labels
  - `test_get_region_names_fr()` — region 34 returns "Mittelland bernois"

- Existing tests in `tests/test_aggregation.py`, `tests/test_briefing.py`, `tests/test_export.py` must remain green — `build_briefing(report, mode)` default `lang="de"` is backward-compatible.

---

## Extensibility note

Adding Italian (IT) later requires:
1. Add `text_blocks_it.py`
2. Add `"it"` entries to `_TREND_LABELS`, `UI_STRINGS`, `CDI_LABELS_IT`, `BERNE_REGION_NAMES_IT`
3. Add `"it"` to the sidebar language radio
4. Add to stlite manifest

No structural changes needed.
