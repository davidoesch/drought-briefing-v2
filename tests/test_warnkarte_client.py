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
