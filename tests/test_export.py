import plotly.graph_objects as go

from src.aggregation.regional import compute_region_report
from src.briefing.template import build_briefing
from src.data.fixture_loader import load
from src.export.report import to_html


def test_to_html_embeds_plotly_not_png():
    bundle = load()
    report = compute_region_report(34, bundle)
    doc = build_briefing(report, "behoerden")
    fig = go.Figure(go.Scatter(x=[1, 2], y=[1, 2]))

    html = to_html(doc, report, chart_fig=fig, map_png=None)

    import re
    assert "plotly" in html.lower(), "Plotly JS must be embedded inline"
    assert not re.search(r'<img[^>]+src=["\']data:image/png;base64', html), (
        "Chart must not be a static PNG <img> tag"
    )
    assert "<!DOCTYPE html>" in html


def test_to_html_without_chart_is_valid():
    bundle = load()
    report = compute_region_report(34, bundle)
    doc = build_briefing(report, "behoerden")

    html = to_html(doc, report, chart_fig=None, map_png=None)

    assert "<!DOCTYPE html>" in html
    assert "plotly" not in html.lower(), "No Plotly when chart_fig is None"
