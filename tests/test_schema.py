"""
tests/test_schema.py

JSON Schema validation tests for the data/processed/ contract.
All tests use fixture data — no network calls, no disk writes.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import jsonschema
import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Load scripts/validate.py via importlib (no __init__.py in scripts/).
_spec = importlib.util.spec_from_file_location(
    "scripts_validate", _REPO_ROOT / "scripts" / "validate.py"
)
_val = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_val)

_load_schema = _val._load_schema
_validate = _val._validate
run_validation = _val.run_validation
validate_regions = _val.validate_regions
validate_cantons = _val.validate_cantons

# Load aggregate helpers for fixture-based serialization.
_agg_spec = importlib.util.spec_from_file_location(
    "scripts_aggregate", _REPO_ROOT / "scripts" / "aggregate.py"
)
_agg = importlib.util.module_from_spec(_agg_spec)
_agg_spec.loader.exec_module(_agg)
_to_json = _agg._to_json

from src.aggregation.canton import compute_canton_report
from src.aggregation.regional import compute_region_report
from src.data import vhi_client as _vhi_client
from src.data import warnkarte_client as _warnkarte_client
from src.data.fixture_loader import load as load_fixture

SCHEMAS_DIR = _REPO_ROOT / "config" / "schemas"


# ---------------------------------------------------------------------------
# Schema file integrity: the schema files themselves are valid JSON Schema
# ---------------------------------------------------------------------------

class TestSchemaFiles:
    def test_region_schema_file_exists(self):
        assert (SCHEMAS_DIR / "region.json").exists()

    def test_canton_schema_file_exists(self):
        assert (SCHEMAS_DIR / "canton.json").exists()

    def test_region_schema_is_valid_json(self):
        raw = (SCHEMAS_DIR / "region.json").read_text(encoding="utf-8")
        schema = json.loads(raw)
        assert isinstance(schema, dict)

    def test_canton_schema_is_valid_json(self):
        raw = (SCHEMAS_DIR / "canton.json").read_text(encoding="utf-8")
        schema = json.loads(raw)
        assert isinstance(schema, dict)

    def test_region_schema_has_required_array(self):
        schema = json.loads((SCHEMAS_DIR / "region.json").read_text())
        assert "required" in schema
        assert len(schema["required"]) > 0

    def test_canton_schema_has_required_array(self):
        schema = json.loads((SCHEMAS_DIR / "canton.json").read_text())
        assert "required" in schema
        assert len(schema["required"]) > 0

    def test_region_schema_required_covers_core_fields(self):
        schema = json.loads((SCHEMAS_DIR / "region.json").read_text())
        req = set(schema["required"])
        for field in ("region_id", "data_timestamp", "cdi", "warnlevel", "quality", "discharge"):
            assert field in req, f"'{field}' missing from required"

    def test_canton_schema_required_covers_core_fields(self):
        schema = json.loads((SCHEMAS_DIR / "canton.json").read_text())
        req = set(schema["required"])
        for field in ("canton_id", "data_timestamp", "max_warnlevel", "regions", "quality"):
            assert field in req, f"'{field}' missing from required"


# ---------------------------------------------------------------------------
# Fixture: shared report objects computed once per test module
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def fixture_bundle():
    return load_fixture()


@pytest.fixture(scope="module")
def region_34_data(fixture_bundle):
    """Region 34 serialized as a dict."""
    wk = _warnkarte_client._load_from_fixture([34])
    vhi = _vhi_client._load_from_fixture([34])
    report = compute_region_report(34, fixture_bundle, wk.get(34), vhi.get(34))
    return json.loads(_to_json(report))


@pytest.fixture(scope="module")
def canton_2_data(fixture_bundle):
    """Canton 2 (Bern) serialized as a dict."""
    bern_ids = [33, 34, 35, 37, 38, 41]
    wk = _warnkarte_client._load_from_fixture(bern_ids)
    vhi = _vhi_client._load_from_fixture(bern_ids)
    orig = _vhi_client.fetch_for_regions
    _vhi_client.fetch_for_regions = lambda rids: {r: vhi[r] for r in rids if r in vhi}
    try:
        report = compute_canton_report(2, fixture_bundle, wk)
    finally:
        _vhi_client.fetch_for_regions = orig
    return json.loads(_to_json(report))


@pytest.fixture(scope="module")
def region_schema():
    return _load_schema("region.json")


@pytest.fixture(scope="module")
def canton_schema():
    return _load_schema("canton.json")


# ---------------------------------------------------------------------------
# Region schema: fixture report passes validation
# ---------------------------------------------------------------------------

class TestRegionSchema:
    def test_region_34_passes_schema(self, region_34_data, region_schema):
        errors: list[str] = []
        assert _validate(region_34_data, region_schema, "region_34", errors), errors

    def test_all_bern_regions_pass_schema(self, fixture_bundle, region_schema):
        bern_ids = [33, 34, 35, 37, 38, 41]
        wk = _warnkarte_client._load_from_fixture(bern_ids)
        vhi = _vhi_client._load_from_fixture(bern_ids)
        for rid in bern_ids:
            report = compute_region_report(rid, fixture_bundle, wk.get(rid), vhi.get(rid))
            data = json.loads(_to_json(report))
            errors: list[str] = []
            ok = _validate(data, region_schema, f"region_{rid}", errors)
            assert ok, f"Region {rid} failed schema: {errors}"

    def test_region_without_warnkarte_passes_schema(self, fixture_bundle, region_schema):
        """Region with no warnkarte entry (uses CDI fallback) still validates."""
        vhi = _vhi_client._load_from_fixture([34])
        report = compute_region_report(34, fixture_bundle, warnkarte_entry=None, vhi_value=vhi.get(34))
        data = json.loads(_to_json(report))
        errors: list[str] = []
        assert _validate(data, region_schema, "region_34_no_warnkarte", errors), errors

    def test_region_with_null_cdi_forecast_passes_schema(self, fixture_bundle, region_schema):
        """Null nullable fields (cdi_forecast_week2 = null) are allowed."""
        # Use an empty forecast bundle to force null forecasts
        import copy
        import pandas as pd
        b = copy.copy(fixture_bundle)
        b.forecast_df = pd.DataFrame()
        vhi = _vhi_client._load_from_fixture([34])
        wk = _warnkarte_client._load_from_fixture([34])
        report = compute_region_report(34, b, wk.get(34), vhi.get(34))
        data = json.loads(_to_json(report))
        assert data["cdi_forecast_week2"] is None
        errors: list[str] = []
        assert _validate(data, region_schema, "region_34_no_forecast", errors), errors

    def test_missing_required_field_fails(self, region_34_data, region_schema):
        """Schema must reject a report with a required field removed."""
        bad = dict(region_34_data)
        del bad["cdi"]
        errors: list[str] = []
        ok = _validate(bad, region_schema, "bad_region", errors)
        assert not ok
        assert errors

    def test_cdi_out_of_range_fails(self, region_34_data, region_schema):
        """cdi=6 must fail validation."""
        bad = {**region_34_data, "cdi": 6}
        errors: list[str] = []
        assert not _validate(bad, region_schema, "bad_cdi", errors)

    def test_invalid_source_fails(self, region_34_data, region_schema):
        """source='unknown' must fail the enum constraint."""
        bad = {**region_34_data, "source": "unknown"}
        errors: list[str] = []
        assert not _validate(bad, region_schema, "bad_source", errors)

    def test_invalid_overall_fails(self, region_34_data, region_schema):
        """quality.overall='bad' must fail the enum constraint."""
        bad = dict(region_34_data)
        bad["quality"] = {**bad["quality"], "overall": "bad"}
        errors: list[str] = []
        assert not _validate(bad, region_schema, "bad_overall", errors)

    def test_extra_field_fails(self, region_34_data, region_schema):
        """additionalProperties: false must reject undocumented fields."""
        bad = {**region_34_data, "undocumented_field": "surprise"}
        errors: list[str] = []
        assert not _validate(bad, region_schema, "extra_field", errors)


# ---------------------------------------------------------------------------
# Canton schema: fixture report passes validation
# ---------------------------------------------------------------------------

class TestCantonSchema:
    def test_canton_2_passes_schema(self, canton_2_data, canton_schema):
        errors: list[str] = []
        assert _validate(canton_2_data, canton_schema, "canton_2", errors), errors

    def test_embedded_regions_pass_region_schema(self, canton_2_data, region_schema):
        """Each embedded region in the canton JSON must also pass the region schema."""
        for i, region_data in enumerate(canton_2_data["regions"]):
            errors: list[str] = []
            ok = _validate(region_data, region_schema, f"canton_2:regions[{i}]", errors)
            assert ok, f"Embedded region {i} failed: {errors}"

    def test_missing_required_field_fails(self, canton_2_data, canton_schema):
        bad = dict(canton_2_data)
        del bad["max_warnlevel"]
        errors: list[str] = []
        assert not _validate(bad, canton_schema, "bad_canton", errors)

    def test_extra_field_fails(self, canton_2_data, canton_schema):
        bad = {**canton_2_data, "undocumented_field": 42}
        errors: list[str] = []
        assert not _validate(bad, canton_schema, "extra_canton_field", errors)

    def test_max_warnlevel_out_of_range_fails(self, canton_2_data, canton_schema):
        bad = {**canton_2_data, "max_warnlevel": 6}
        errors: list[str] = []
        assert not _validate(bad, canton_schema, "bad_max_warnlevel", errors)

    def test_cdi_min_dry_null_passes(self, canton_2_data, canton_schema):
        """cdi_min_dry = null is allowed (no dry regions)."""
        data = {**canton_2_data, "cdi_min_dry": None, "cdi_max_dry": None}
        errors: list[str] = []
        assert _validate(data, canton_schema, "canton_no_dry", errors), errors

    def test_regions_must_be_nonempty(self, canton_2_data, canton_schema):
        """Canton with no regions must fail (minItems: 1)."""
        bad = {**canton_2_data, "regions": []}
        errors: list[str] = []
        assert not _validate(bad, canton_schema, "empty_regions", errors)


# ---------------------------------------------------------------------------
# validate.py integration: run_validation against a tmp processed directory
# ---------------------------------------------------------------------------

class TestValidateScript:
    def _write_processed(self, tmp_path: Path, region_data: dict, canton_data: dict) -> Path:
        """Write fixture reports to a tmp processed directory."""
        (tmp_path / "warning_regions").mkdir()
        (tmp_path / "cantons").mkdir()
        (tmp_path / "warning_regions" / "34.json").write_text(
            json.dumps(region_data), encoding="utf-8"
        )
        (tmp_path / "cantons" / "2.json").write_text(
            json.dumps(canton_data), encoding="utf-8"
        )
        return tmp_path

    def test_valid_outputs_produce_no_errors(self, tmp_path, region_34_data, canton_2_data):
        processed = self._write_processed(tmp_path, region_34_data, canton_2_data)
        errors = run_validation(processed)
        assert errors == []

    def test_invalid_region_produces_errors(self, tmp_path, region_34_data, canton_2_data):
        bad_region = {**region_34_data, "cdi": 99}  # out of range
        processed = self._write_processed(tmp_path, bad_region, canton_2_data)
        errors = run_validation(processed)
        assert any("34.json" in e or "region" in e.lower() for e in errors)

    def test_invalid_canton_produces_errors(self, tmp_path, region_34_data, canton_2_data):
        bad_canton = {**canton_2_data, "max_warnlevel": 0}  # below minimum of 1
        processed = self._write_processed(tmp_path, region_34_data, bad_canton)
        errors = run_validation(processed)
        assert any("2.json" in e or "canton" in e.lower() for e in errors)

    def test_missing_processed_dir_returns_no_errors(self, tmp_path):
        """Non-existent sub-directories produce warnings, not errors."""
        errors = run_validation(tmp_path)
        assert errors == []

    def test_embedded_region_violation_caught(self, tmp_path, region_34_data, canton_2_data):
        """An invalid embedded region inside a canton JSON is detected."""
        bad_region_embed = {**region_34_data, "warnlevel": 6}  # out of range
        bad_canton = dict(canton_2_data)
        bad_canton["regions"] = [bad_region_embed]
        processed = self._write_processed(tmp_path, region_34_data, bad_canton)
        errors = run_validation(processed)
        # The embedded region validation should catch the warnlevel=6 violation
        assert len(errors) > 0
