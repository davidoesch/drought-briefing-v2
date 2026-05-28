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
