"""
tests/test_aggregate_script.py

Aggregation consistency tests for scripts/aggregate.py.
All tests use bundled fixture data — no network calls required.
"""
from __future__ import annotations

import importlib.util
import json
import math
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Load scripts/aggregate.py without requiring it to be a package.
_spec = importlib.util.spec_from_file_location(
    "scripts_aggregate", _REPO_ROOT / "scripts" / "aggregate.py"
)
_agg = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_agg)

_nan_to_none = _agg._nan_to_none
_to_json = _agg._to_json
_load_warnkarte = _agg._load_warnkarte
_load_vhi = _agg._load_vhi

from src.aggregation.regional import compute_region_report
from src.data import vhi_client as _vhi_client
from src.data import warnkarte_client as _warnkarte_client
from src.data.fixture_loader import load as load_fixture


# ---------------------------------------------------------------------------
# _nan_to_none — pure unit tests
# ---------------------------------------------------------------------------

class TestNanToNone:
    def test_nan_becomes_none(self):
        assert _nan_to_none(float("nan")) is None

    def test_inf_becomes_none(self):
        assert _nan_to_none(float("inf")) is None

    def test_neg_inf_becomes_none(self):
        assert _nan_to_none(float("-inf")) is None

    def test_normal_float_unchanged(self):
        assert _nan_to_none(3.14) == pytest.approx(3.14)

    def test_integer_unchanged(self):
        assert _nan_to_none(42) == 42

    def test_none_unchanged(self):
        assert _nan_to_none(None) is None

    def test_string_unchanged(self):
        assert _nan_to_none("hello") == "hello"

    def test_dict_recursive(self):
        result = _nan_to_none({"a": float("nan"), "b": 2.0})
        assert result["a"] is None
        assert result["b"] == pytest.approx(2.0)

    def test_list_recursive(self):
        result = _nan_to_none([float("nan"), 1.0, float("inf")])
        assert result == [None, pytest.approx(1.0), None]

    def test_nested_structure(self):
        result = _nan_to_none({"inner": {"x": float("nan"), "y": [float("nan"), 1]}})
        assert result["inner"]["x"] is None
        assert result["inner"]["y"][0] is None
        assert result["inner"]["y"][1] == 1


# ---------------------------------------------------------------------------
# _to_json — serialization of a real RegionReport
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def region_34_report():
    """Region 34 (Berner Mittelland) computed from fixture data."""
    bundle = load_fixture()
    warnkarte = _warnkarte_client._load_from_fixture([34])
    vhi = _vhi_client._load_from_fixture([34])
    return compute_region_report(34, bundle, warnkarte.get(34), vhi.get(34))


class TestToJson:
    def test_produces_valid_json(self, region_34_report):
        data = json.loads(_to_json(region_34_report))
        assert isinstance(data, dict)

    def test_no_nan_string_in_output(self, region_34_report):
        assert "NaN" not in _to_json(region_34_report)

    def test_datetime_serialized_as_iso_string(self, region_34_report):
        data = json.loads(_to_json(region_34_report))
        ts = data["data_timestamp"]
        assert isinstance(ts, str)
        assert "T" in ts  # ISO-8601 datetime separator

    def test_required_fields_present(self, region_34_report):
        data = json.loads(_to_json(region_34_report))
        for field in (
            "region_id", "region_name_de", "data_timestamp", "source",
            "cdi", "warnlevel", "precip_1m_index", "soil_moisture_index",
            "hydro_index", "discharge", "quality",
        ):
            assert field in data, f"Missing field: {field}"

    def test_warnlevel_in_valid_range(self, region_34_report):
        data = json.loads(_to_json(region_34_report))
        assert 1 <= data["warnlevel"] <= 5

    def test_cdi_in_valid_range(self, region_34_report):
        data = json.loads(_to_json(region_34_report))
        assert 0 <= data["cdi"] <= 5

    def test_index_fields_in_valid_range(self, region_34_report):
        data = json.loads(_to_json(region_34_report))
        for field in ("precip_1m_index", "soil_moisture_index", "hydro_index"):
            assert 1 <= data[field] <= 5, f"{field} out of range: {data[field]}"

    def test_discharge_structure_consistent(self, region_34_report):
        data = json.loads(_to_json(region_34_report))
        d = data["discharge"]
        assert d["n_low"] <= d["n_total"]
        assert d["n_very_low"] <= d["n_low"]
        if d["n_total"] > 0:
            assert d["pct_low"] == round(d["n_low"] / d["n_total"] * 100)


# ---------------------------------------------------------------------------
# Aggregation consistency — JSON values match compute_region_report() directly
# ---------------------------------------------------------------------------

class TestAggregationConsistency:
    """Verify that _to_json(compute_region_report(...)) roundtrips correctly."""

    def test_region_id_preserved(self, region_34_report):
        data = json.loads(_to_json(region_34_report))
        assert data["region_id"] == region_34_report.region_id

    def test_cdi_preserved(self, region_34_report):
        data = json.loads(_to_json(region_34_report))
        assert data["cdi"] == region_34_report.cdi

    def test_warnlevel_preserved(self, region_34_report):
        data = json.loads(_to_json(region_34_report))
        assert data["warnlevel"] == region_34_report.warnlevel

    def test_precip_1m_index_preserved(self, region_34_report):
        data = json.loads(_to_json(region_34_report))
        assert data["precip_1m_index"] == region_34_report.precip_1m_index

    def test_soil_moisture_index_preserved(self, region_34_report):
        data = json.loads(_to_json(region_34_report))
        assert data["soil_moisture_index"] == region_34_report.soil_moisture_index

    def test_spi_3m_preserved_or_null(self, region_34_report):
        data = json.loads(_to_json(region_34_report))
        if math.isnan(region_34_report.spi_3m):
            assert data["spi_3m"] is None
        else:
            assert data["spi_3m"] == pytest.approx(region_34_report.spi_3m)

    def test_pct_critical_preserved(self, region_34_report):
        data = json.loads(_to_json(region_34_report))
        assert data["pct_critical"] == pytest.approx(region_34_report.pct_critical)

    def test_quality_overall_preserved(self, region_34_report):
        data = json.loads(_to_json(region_34_report))
        assert data["quality"]["overall"] == region_34_report.quality.overall


# ---------------------------------------------------------------------------
# Fallback loading — no raw data, uses bundled fixtures
# ---------------------------------------------------------------------------

class TestFallbackLoading:
    def test_warnkarte_fallback_returns_entries(self, tmp_path):
        result = _load_warnkarte(tmp_path / "nonexistent")
        assert len(result) > 0
        for entry in result.values():
            assert 1 <= entry.warnlevel <= 5

    def test_vhi_fallback_returns_float_values(self, tmp_path):
        result = _load_vhi(tmp_path / "nonexistent")
        assert len(result) > 0
        for val in result.values():
            assert isinstance(val, float)
            assert not math.isnan(val)

    def test_warnkarte_fallback_covers_bern_regions(self, tmp_path):
        result = _load_warnkarte(tmp_path / "nonexistent")
        for rid in (33, 34, 35, 37, 38, 41):
            assert rid in result, f"Bern region {rid} missing from Warnkarte fallback"


# ---------------------------------------------------------------------------
# Conditional: test raw loading if data/raw/ is present
# ---------------------------------------------------------------------------

_RAW_DIR = _REPO_ROOT / "data" / "raw"

@pytest.mark.skipif(
    not (_RAW_DIR / "current.zip").exists(),
    reason="data/raw/ not present; run scripts/download.py first",
)
class TestLoadFromRaw:
    def test_bundle_from_raw_has_current_data(self):
        bundle = _agg._load_bundle_from_raw(_RAW_DIR)
        assert not bundle.current_df.empty
        assert "drought_region_id" in bundle.current_df.columns
        assert "cdi" in bundle.current_df.columns

    def test_bundle_from_raw_has_historic_data(self):
        bundle = _agg._load_bundle_from_raw(_RAW_DIR)
        assert not bundle.historic_df.empty

    def test_bundle_from_raw_has_timestamp(self):
        bundle = _agg._load_bundle_from_raw(_RAW_DIR)
        assert isinstance(bundle.data_timestamp, __import__("datetime").datetime)

    def test_warnkarte_from_raw_has_all_regions(self):
        result = _load_warnkarte(_RAW_DIR)
        assert len(result) == len(_agg.REGION_NAMES_DE)

    def test_vhi_from_raw_has_values(self):
        result = _load_vhi(_RAW_DIR)
        assert len(result) > 0
