# src/viz/maps.py
from __future__ import annotations
import json
import folium

from config.settings import CDI_COLOURS, GEOJSON_FIXTURE
from src.models import CantonReport, MapSpec, RegionReport

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


def build_canton_map(canton: CantonReport, map_spec: MapSpec) -> folium.Map:
    """
    Folium map showing CDI per warning region of the canton.

    Dispatches on map_spec.id:
    - "cdi_current"         uses RegionReport.cdi
    - "cdi_forecast_week2"  uses RegionReport.cdi_forecast_week2 (falls back to 0 if None)
    """
    if map_spec.id == "cdi_current":
        values = {r.region_id: r.cdi for r in canton.regions}
    elif map_spec.id == "cdi_forecast_week2":
        values = {
            r.region_id: r.cdi_forecast_week2 if r.cdi_forecast_week2 is not None else 0
            for r in canton.regions
        }
    else:
        raise ValueError(
            f"Unknown map_spec.id {map_spec.id!r}. "
            "Expected 'cdi_current' or 'cdi_forecast_week2'."
        )

    return _build_folium_choropleth(values)


def _build_folium_choropleth(values: dict[int, int]) -> folium.Map:
    """Render a values dict {region_id: cdi} as a folium choropleth using the bundled GeoJSON."""
    geo = json.loads(GEOJSON_FIXTURE.read_text())
    m = folium.Map(location=[46.8, 7.4], zoom_start=8, tiles="cartodbpositron")

    def style_fn(feature):
        rid = int(feature["properties"]["drought_region_id"])
        cdi = values.get(rid, 0)
        return {
            "fillColor": CDI_COLOURS.get(cdi, "#cccccc"),
            "color": "#333333",
            "weight": 1,
            "fillOpacity": 0.75,
        }

    folium.GeoJson(geo, style_function=style_fn).add_to(m)
    return m
