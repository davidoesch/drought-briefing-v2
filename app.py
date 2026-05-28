# app.py
"""One Click Drought Briefing — Streamlit entry point for Kanton Bern."""
from __future__ import annotations

import logging
import math
from pathlib import Path
import streamlit as st

from config.settings import CANTON_NAMES, CANTON_TO_REGIONS
from src.aggregation.canton import compute_canton_report
from src.briefing.renderer import load_ruleset, render_briefing
from src.data.stac_client import load as load_data
from src.data.warnkarte_client import fetch_for_regions
from src.export.report import to_html
from src.i18n.strings import t
from src.models import DataBundle
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


# ── Sidebar ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("💧 Trockenheitsbriefing")
    st.caption("Kanton Bern · trockenheit.admin.ch")
    st.divider()

    lang = st.radio(
        "Sprache / Langue",
        options=["de", "fr"],
        format_func=lambda l: "Deutsch" if l == "de" else "Français",
        horizontal=True,
        index=0,
    )

    canton_options = sorted(CANTON_TO_REGIONS.keys())
    selected_canton_id = st.selectbox(
        "Kanton",
        options=canton_options,
        format_func=lambda cid: CANTON_NAMES[cid].get(lang, CANTON_NAMES[cid]["de"]),
        index=0,
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
doc = render_briefing(canton, _ruleset(), locale=lang)

# ── Header ─────────────────────────────────────────────────────────────────
# NOTE: transient broken state — header + sections migrated in Tasks 8.3 + 8.4
col_title, col_badge = st.columns([4, 1])
with col_title:
    st.title(t("briefing_title", lang))
    st.caption(
        f"Kanton {canton.canton_name_de} · "
        f"{t('stand', lang)}: {canton.data_timestamp.strftime('%d.%m.%Y')} · "
        f"{t('source', lang)}: {canton.source}"
    )
with col_badge:
    st.markdown(
        f"""<div style="border-radius:10px;padding:12px;text-align:center;background:#888;">
        <div style="font-size:11px;color:rgba(255,255,255,0.8);">Stufe</div>
        <div style="font-size:36px;font-weight:bold;color:white;">{canton.max_warnlevel}</div>
        </div>""",
        unsafe_allow_html=True,
    )

st.divider()

# ── Text sections (transient — replaced in Task 8.4) ──────────────────────
st.divider()
for section_key in ["lage", "entwicklung", "einordnung"]:
    sec_text = doc.sections.get(section_key, "")
    if sec_text:
        st.markdown(f"**{section_key}**")
        st.markdown(sec_text)
        st.write("")

# ── Quality panel ──────────────────────────────────────────────────────────
with st.expander(t("quality_expander", lang)):
    q = canton.quality
    q_colour = {"ok": "🟢", "warning": "🟡", "error": "🔴"}.get(q.overall, "⚪")
    st.markdown(
        f"{q_colour} **{q.overall.upper()}** — "
        f"{t('data_age', lang)}: {q.data_age_days} Tage — "
        f"{t('coverage', lang)}: {q.coverage_pct:.0%}"
    )
    if q.missing_columns:
        st.warning(f"{t('quality_missing_cols', lang)}: {', '.join(q.missing_columns)}")
    if q.outlier_flags:
        st.warning(f"{t('quality_outliers', lang)}: {', '.join(q.outlier_flags)}")

# ── Export buttons ─────────────────────────────────────────────────────────
with export_placeholder:
    if False:  # disabled until Phase 8b rewrites to_html for CantonReport
        html_str = to_html(doc, canton)
        st.download_button(
            label=t("btn_html", lang),
            data=html_str.encode("utf-8"),
            file_name=f"trockenheit_{canton.data_timestamp.strftime('%Y%m%d')}.html",
            mime="text/html",
        )
    else:
        st.info(t("pdf_hint", lang))
