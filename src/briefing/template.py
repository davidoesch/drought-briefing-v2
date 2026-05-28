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
