# tests/test_models.py
from src.models import MapSpec


def test_map_spec_construction():
    spec = MapSpec(
        id="cdi_current",
        title_de="Aktueller CDI",
        title_fr="CDI actuel",
        source="canton.regions[*].cdi",
        style="choropleth_warnregionen",
    )
    assert spec.id == "cdi_current"
    assert spec.style == "choropleth_warnregionen"


from datetime import datetime

from src.models import WarnkarteEntry


def test_warnkarte_entry_construction():
    entry = WarnkarteEntry(
        drought_region_id=34,
        warnlevel=2,
        info_de="Mässige Gefahr",
        info_fr="Danger limité",
        info_it="Pericolo moderato",
        valid_from=datetime(2026, 5, 28),
    )
    assert entry.warnlevel == 2
    assert entry.info_de == "Mässige Gefahr"
