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

    html_str = to_html(doc, canton, ruleset)

    assert "Bern" in html_str
    assert "Mässige Gefahr" in html_str
    # Human-readable section title (not YAML key) when ruleset is passed
    assert "Allgemeine Lage" in html_str


def test_to_html_fr_locale():
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
    doc = render_briefing(canton, ruleset, locale="fr")

    html_str = to_html(doc, canton, ruleset)

    assert "Bulletin de sécheresse" in html_str  # FR title
    assert "Berne" in html_str  # FR canton name
    assert 'lang="fr"' in html_str  # html lang attribute
    assert "Trockenheit" not in html_str  # no DE text bleeding through
