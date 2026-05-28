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


@responses.activate
def test_fetch_for_regions_falls_back_to_fixture(recwarn):
    base = "https://api3.geo.admin.ch/rest/services/api/MapServer/ch.bafu.trockenheitswarnkarte"
    responses.add(responses.GET, f"{base}/34", status=503)

    out = fetch_for_regions([34])

    # Fixture must contain region 34
    assert 34 in out
    # The function should have emitted a warning about the fallback
    assert any("fetch failed" in str(w.message) for w in recwarn.list)
