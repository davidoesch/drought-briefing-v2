from datetime import datetime
from pathlib import Path

from src.aggregation.canton import compute_canton_report
from src.briefing.renderer import load_ruleset, render_briefing
from src.data.stac_client import load as load_data
from src.export.report import to_html
from src.models import WarnkarteEntry


def test_to_html_contains_canton_name_and_sections():
    bundle = load_data()
    warnkarte = {
        rid: WarnkarteEntry(
            drought_region_id=rid,
            warnlevel=2,
            info_de="Mässige Gefahr",
            info_fr="Danger limité",
            info_it="-",
            valid_from=datetime(2026, 5, 28),
        )
        for rid in [33, 34, 35, 37, 38, 41]
    }
    canton = compute_canton_report(canton_id=2, bundle=bundle, warnkarte_data=warnkarte)
    ruleset = load_ruleset(Path("data/ruleset/canton-bulletin.yaml"))
    doc = render_briefing(canton, ruleset, locale="de")

    html = to_html(doc, canton)

    assert "Bern" in html
    assert "Mässige Gefahr" in html
    assert "allgemeine-lage" in html
