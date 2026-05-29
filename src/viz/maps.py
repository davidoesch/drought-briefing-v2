# src/viz/maps.py
from __future__ import annotations
import json
import folium

from config.settings import CDI_COLOURS, GEOJSON_FIXTURE
from src.models import RegionReport

def _load_geojson() -> dict:
    if GEOJSON_FIXTURE.exists():
        with open(GEOJSON_FIXTURE, "r", encoding="utf-8") as f:
            return json.load(f)
    raise FileNotFoundError(f"GeoJSON fixture not found: {GEOJSON_FIXTURE}")

def build_map(
    selected_report: RegionReport,
    all_reports: list[RegionReport],
) -> folium.Map:
    geo_data = _load_geojson()
    cdi_by_id = {r.region_id: r.cdi for r in all_reports}

    m = folium.Map(
        location=[46.80, 7.55],
        zoom_start=9,
        tiles="CartoDB positron",
    )

    def style_fn(feature):
        rid = feature["properties"]["drought_region_id"]
        cdi = cdi_by_id.get(rid, 0)
        is_selected = rid == selected_report.region_id
        return {
            "fillColor": CDI_COLOURS.get(cdi, "#cccccc"),
            "color": "#ffffff" if is_selected else "#888888",
            "weight": 3 if is_selected else 1,
            "fillOpacity": 0.5,
        }

    folium.GeoJson(
        geo_data,
        style_function=style_fn,
        tooltip=folium.GeoJsonTooltip(
            fields=["drought_region_id", "name_de"],
            aliases=["Region-ID:", "Name:"],
        ),
    ).add_to(m)

    return m