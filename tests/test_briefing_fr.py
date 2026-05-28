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
