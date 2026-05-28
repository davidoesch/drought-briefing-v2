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
