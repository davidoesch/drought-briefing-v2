# app.py
"""One Click Drought Briefing — Streamlit entry point for Kanton Bern."""
from __future__ import annotations

import logging
import math
from pathlib import Path
import streamlit as st

from config.settings import CANTON_NAMES, CANTON_TO_REGIONS, CDI_COLOURS
from src.aggregation.canton import compute_canton_report
from src.briefing.renderer import load_ruleset, render_briefing
from src.data.stac_client import load as load_data
from src.data.warnkarte_client import fetch_for_regions
from src.export.report import to_html
from src.i18n.strings import get_cdi_labels, get_region_names, t
from src.models import DataBundle
from src.viz.charts import build_timeseries
from src.viz.maps import build_canton_map

st.set_page_config(
    page_title="Trockenheitsbriefing / Bulletin sécheresse",
    page_icon="💧",
    layout="wide",
)

@st.cache_data(ttl=3600, show_spinner="Daten werden geladen…")
def _load_bundle() -> DataBundle:
    return load_data()

@st.cache_data(ttl=3600, show_spinner="Warnstufen werden geladen…")
def _load_warnkarte(region_ids: tuple[int, ...]):
    return fetch_for_regions(list(region_ids))

@st.cache_resource
def _ruleset():
    return load_ruleset(Path("data/ruleset/canton-bulletin.yaml"))

def _warnstufe_palette(level: int) -> tuple[str, str]:
    """Return (background, text) colour pair for a warning level (1–5)."""
    palette = {
        1: ("#6bbd50", "#ffffff"),
        2: ("#f7e84c", "#1a1a1a"),
        3: ("#ff8c00", "#ffffff"),
        4: ("#e02020", "#ffffff"),
        5: ("#8b0000", "#ffffff"),
    }
    return palette.get(level, ("#cccccc", "#1a1a1a"))

def _get_recommendations(warnlevel: int, lang: str, rs) -> list[str]:
    """Resolve recommendations handling fallback chains."""
    he = rs.handlungsempfehlungen.by_gefahrenstufe
    current = he.get(warnlevel)
    seen = set()
    while current and current.empfehlungen is None and current.fallback is not None:
        if current.fallback in seen: 
            break
        seen.add(current.fallback)
        current = he.get(current.fallback)
    if current and current.empfehlungen:
        return current.empfehlungen.get(lang, [])
    return []


# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    lang = st.radio(
        "Sprache / Langue",
        options=["de", "fr"],
        format_func=lambda l: "Deutsch" if l == "de" else "Français",
        horizontal=True,
        index=0,
    )

    st.title(t("sidebar_title", lang))
    st.caption(t("sidebar_caption", lang))
    st.divider()

    canton_options = sorted(CANTON_TO_REGIONS.keys())
    selected_canton_id = st.selectbox(
        t("canton_label", lang),
        options=canton_options,
        format_func=lambda cid: CANTON_NAMES[cid].get(lang, CANTON_NAMES[cid]["de"]),
        index=0,
    )
    
    st.divider()
    
    view_tab = st.radio(
        "Navigation",
        options=["canton", "regions"],
        format_func=lambda x: t(f"tab_{x}", lang),
        label_visibility="collapsed"
    )

    st.divider()

    bundle = _load_bundle()
    st.caption(f"{t('data_status', lang)}: {bundle.data_timestamp.strftime('%d.%m.%Y')}")
    st.caption(f"{t('source', lang)}: {bundle.source}")

    st.divider()
    st.subheader(t("export_header", lang))
    export_placeholder = st.empty()


# ── Pipeline ───────────────────────────────────────────────────────────────
region_ids = tuple(sorted(CANTON_TO_REGIONS[selected_canton_id]))
warnkarte = _load_warnkarte(region_ids)
canton = compute_canton_report(
    canton_id=selected_canton_id,
    bundle=bundle,
    warnkarte_data=warnkarte,
)
rs = _ruleset()
doc = render_briefing(canton, rs, locale=lang)

canton_label = canton.canton_name_de if lang == "de" else canton.canton_name_fr


# ── Tab 1: Allgemeine Lage (Kanton) ────────────────────────────────────────
if view_tab == "canton":
    st.title(f"{t('export_doc_title', lang)} {canton_label}")
    bg, text_colour = _warnstufe_palette(canton.max_warnlevel)
    st.markdown(
        f"""<div style="background:{bg};border-radius:8px;padding:18px;color:{text_colour};">
        <div style="font-size:11px;opacity:.85;">{t("current_warnlevel", lang)}</div>
        <div style="font-size:28px;font-weight:700;">{doc.lead_headline}</div>
        <div style="font-size:12px;opacity:.85;">{doc.lead_meta}</div>
        </div>""",
        unsafe_allow_html=True,
    )

    st.divider()

    map_cols = st.columns(2)
    for col, map_spec in zip(map_cols, doc.lead_maps):
        with col:
            st.subheader(map_spec.title_de if lang == "de" else map_spec.title_fr)
            m = build_canton_map(canton, map_spec)
            st.components.v1.html(m._repr_html_(), height=300)

    st.divider()

    for sec in rs.sections:
        # Exclude the 'regionen' section from the main tab to avoid redundancy
        if sec.id == "regionen":
            continue
            
        title = sec.title.get(lang, sec.title.get("de", sec.id))
        st.markdown(f"## {title}")
        st.markdown(doc.sections[sec.id])
        st.write("")

# ── Tab 2: Regionale Lage ──────────────────────────────────────────────────
elif view_tab == "regions":
    st.title(f"{t('tab_regions', lang)}: {canton_label}")
    st.divider()
    
    table_html = [
        "<table style='width: 100%; text-align: left; border-collapse: collapse; font-family: sans-serif;'>",
        "<thead><tr style='border-bottom: 2px solid #ddd; background-color: rgba(0,0,0,0.05);'>",
        f"<th style='padding: 12px 8px;'>{t('col_warnstufe', lang)}</th>",
        f"<th style='padding: 12px 8px;'>{t('col_region', lang)}</th>",
        f"<th style='padding: 12px 8px;'>{t('col_situation', lang)}</th>",
        f"<th style='padding: 12px 8px;'>{t('col_empfehlungen', lang)}</th>",
        f"<th style='padding: 12px 8px;'>{t('col_link', lang)}</th>",
        "</tr></thead><tbody>"
    ]

    for r in canton.regions:
        # 1. Warnstufe Badge
        bg, fg = _warnstufe_palette(r.warnlevel)
        badge = f"<div style='background:{bg}; color:{fg}; padding:6px; border-radius:6px; text-align:center; font-weight:bold; width:max-content; min-width:30px;'>{r.warnlevel}</div>"
        
        # 2. Region Name
        name = get_region_names(lang).get(r.region_id, r.region_name_de)
        
        # 3. Situation
        cdi_label = get_cdi_labels(lang).get(r.cdi, t("unknown", lang))
        spi_val = f"{r.spi_3m:.2f}" if not math.isnan(r.spi_3m) else "–"
        soil_val = f"{r.soil_moisture_pct:.0f}%" if not math.isnan(r.soil_moisture_pct) else "–"
        situation = f"<b>CDI {r.cdi} ({cdi_label})</b><br/><span style='color:#555;'>{t('metric_spi', lang)}: {spi_val}<br/>{t('metric_soil', lang)}: {soil_val}</span>"
        
        # 4. Empfehlungen
        recs = _get_recommendations(r.warnlevel, lang, rs)
        if recs:
            recs_html = "<ul style='margin:0; padding-left:20px; color:#333;'>" + "".join(f"<li style='margin-bottom:6px;'>{item}</li>" for item in recs) + "</ul>"
        else:
            recs_html = f"<span style='color:#999;'>—</span>"
            
        # 5. Link
        link_url = f"https://www.trockenheit.admin.ch/{lang}/regionen/{r.region_id}/aktuelle-lage"
        link_html = f"<a href='{link_url}' target='_blank' style='text-decoration:none; font-weight:600;'>{t('link_details', lang)} ↗</a>"

        table_html.append(
            f"<tr style='border-bottom: 1px solid #eee; vertical-align: top;'>"
            f"<td style='padding: 16px 8px;'>{badge}</td>"
            f"<td style='padding: 16px 8px;'><b>{name}</b></td>"
            f"<td style='padding: 16px 8px; font-size: 14px; min-width:180px;'>{situation}</td>"
            f"<td style='padding: 16px 8px; font-size: 14px;'>{recs_html}</td>"
            f"<td style='padding: 16px 8px;'>{link_html}</td>"
            f"</tr>"
        )
        
    table_html.append("</tbody></table>")
    st.markdown("".join(table_html), unsafe_allow_html=True)


# ── Global Footer (Applies to both tabs) ───────────────────────────────────
st.divider()

with st.expander(t("quality_expander", lang)):
    q = canton.quality
    q_colour = {"ok": "🟢", "warning": "🟡", "error": "🔴"}.get(q.overall, "⚪")
    st.markdown(
        f"{q_colour} **{q.overall.upper()}** — "
        f"{t('data_age', lang)}: {q.data_age_days} {t('days', lang)} — "
        f"{t('coverage', lang)}: {q.coverage_pct:.0%}"
    )
    if q.missing_columns:
        st.warning(f"{t('quality_missing_cols', lang)}: {', '.join(q.missing_columns)}")
    if q.outlier_flags:
        st.warning(f"{t('quality_outliers', lang)}: {', '.join(q.outlier_flags)}")
    
    for r in canton.regions:
        st.caption(
            f"R{r.region_id} ({r.region_name_de}): "
            f"{r.quality.overall} — {t('coverage', lang)} {r.quality.coverage_pct:.0%}"
        )

with export_placeholder:
    html_str = to_html(doc, canton, rs)
    st.download_button(
        label=t("btn_html", lang),
        data=html_str.encode("utf-8"),
        file_name=f"trockenheit_{canton.data_timestamp.strftime('%Y%m%d')}.html",
        mime="text/html",
    )