# src/export/report.py
from __future__ import annotations

from src.models import BriefingDocument, CantonReport


def to_html(
    doc: BriefingDocument,
    canton_report: CantonReport,
    chart_fig=None,
    map_png: bytes | None = None,
) -> str:
    title = f"Trockenheitsbriefing {canton_report.canton_name_de}"
    badge_colour = {
        1: "#6bbd50", 2: "#f7e84c", 3: "#ff8c00", 4: "#e02020", 5: "#8b0000",
    }.get(canton_report.max_warnlevel, "#cccccc")
    badge_html = (
        f'<div style="background:{badge_colour};color:#fff;padding:14px;border-radius:6px;">'
        f'<div style="font-size:24px;font-weight:700;">{doc.lead_headline}</div>'
        f'<div style="font-size:11px;opacity:.85;">{doc.lead_meta}</div>'
        f'</div>'
    )
    sections_html = "\n".join(
        f'<section><h2>{sec_id}</h2><div>{body}</div></section>'
        for sec_id, body in doc.sections.items()
    )
    return f"""<!DOCTYPE html>
<html lang="{doc.locale}">
<head><meta charset="UTF-8"><title>{title}</title></head>
<body>
<header><h1>{title}</h1>{badge_html}</header>
<main>{sections_html}</main>
</body>
</html>"""
