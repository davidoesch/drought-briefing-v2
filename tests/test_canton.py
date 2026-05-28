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
