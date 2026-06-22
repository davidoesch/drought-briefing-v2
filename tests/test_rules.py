"""
tests/test_rules.py

YAML schema validation and regression tests for config/rules.yaml.
Verifies that the rule engine loads correctly and that hardcoded baseline
values are preserved.
"""
from __future__ import annotations

import math
from pathlib import Path

import pytest
import yaml

from config.rules_loader import RULES, Rules, load_rules

_RULES_PATH = Path(__file__).resolve().parents[1] / "config" / "rules.yaml"


# ---------------------------------------------------------------------------
# YAML structure: required keys present
# ---------------------------------------------------------------------------

class TestYamlSchema:
    def test_file_exists(self):
        assert _RULES_PATH.exists()

    def test_required_top_level_sections(self):
        raw = yaml.safe_load(_RULES_PATH.read_text(encoding="utf-8"))
        for section in ("data_quality", "cdi", "indicator_deficits", "historic", "forecast", "warnlevel"):
            assert section in raw, f"Missing top-level section: {section}"

    def test_data_quality_keys(self):
        raw = yaml.safe_load(_RULES_PATH.read_text(encoding="utf-8"))
        dq = raw["data_quality"]
        for key in ("staleness_days", "coverage_error_threshold", "outlier_iqr_factor", "indicator_columns"):
            assert key in dq, f"Missing data_quality key: {key}"

    def test_cdi_keys(self):
        raw = yaml.safe_load(_RULES_PATH.read_text(encoding="utf-8"))
        cdi = raw["cdi"]
        for key in ("critical_min", "dry_min"):
            assert key in cdi, f"Missing cdi key: {key}"

    def test_indicator_deficits_keys(self):
        raw = yaml.safe_load(_RULES_PATH.read_text(encoding="utf-8"))
        ind = raw["indicator_deficits"]
        for key in ("precip_1m_index_min", "soil_moisture_index_min"):
            assert key in ind, f"Missing indicator_deficits key: {key}"

    def test_historic_keys(self):
        raw = yaml.safe_load(_RULES_PATH.read_text(encoding="utf-8"))
        assert "window_weeks" in raw["historic"]

    def test_forecast_keys(self):
        raw = yaml.safe_load(_RULES_PATH.read_text(encoding="utf-8"))
        fc = raw["forecast"]
        for key in ("horizon_days", "max_delta_days"):
            assert key in fc, f"Missing forecast key: {key}"

    def test_warnlevel_keys(self):
        raw = yaml.safe_load(_RULES_PATH.read_text(encoding="utf-8"))
        assert "fallback_min" in raw["warnlevel"]

    def test_indicator_columns_is_list(self):
        raw = yaml.safe_load(_RULES_PATH.read_text(encoding="utf-8"))
        assert isinstance(raw["data_quality"]["indicator_columns"], list)
        assert len(raw["data_quality"]["indicator_columns"]) > 0


# ---------------------------------------------------------------------------
# Rules object: correct types
# ---------------------------------------------------------------------------

class TestRulesTypes:
    def test_staleness_days_is_int(self):
        assert isinstance(RULES.staleness_days, int)

    def test_coverage_error_threshold_is_float(self):
        assert isinstance(RULES.coverage_error_threshold, float)

    def test_outlier_iqr_factor_is_float(self):
        assert isinstance(RULES.outlier_iqr_factor, float)

    def test_indicator_columns_is_list_of_str(self):
        assert isinstance(RULES.indicator_columns, list)
        assert all(isinstance(c, str) for c in RULES.indicator_columns)

    def test_cdi_critical_min_is_int(self):
        assert isinstance(RULES.cdi_critical_min, int)

    def test_cdi_dry_min_is_int(self):
        assert isinstance(RULES.cdi_dry_min, int)

    def test_precip_1m_index_min_is_int(self):
        assert isinstance(RULES.precip_1m_index_min, int)

    def test_soil_moisture_index_min_is_int(self):
        assert isinstance(RULES.soil_moisture_index_min, int)

    def test_window_weeks_is_int(self):
        assert isinstance(RULES.window_weeks, int)

    def test_horizon_days_is_int(self):
        assert isinstance(RULES.horizon_days, int)

    def test_max_delta_days_is_int(self):
        assert isinstance(RULES.max_delta_days, int)

    def test_fallback_min_is_int(self):
        assert isinstance(RULES.fallback_min, int)


# ---------------------------------------------------------------------------
# Baseline values: regression test (must match pre-refactor constants)
# ---------------------------------------------------------------------------

class TestBaselineValues:
    def test_staleness_days(self):
        assert RULES.staleness_days == 14

    def test_coverage_error_threshold(self):
        assert RULES.coverage_error_threshold == pytest.approx(0.5)

    def test_outlier_iqr_factor(self):
        assert RULES.outlier_iqr_factor == pytest.approx(3.0)

    def test_indicator_columns(self):
        expected = [
            "cdi", "spi_3m", "soil_moisture_ufc", "vhi",
            "spi_1m", "spi_6m", "spi_12m", "spi_24m",
            "precip_sum_1m", "precip_sum_3m",
        ]
        assert RULES.indicator_columns == expected

    def test_cdi_critical_min(self):
        assert RULES.cdi_critical_min == 3

    def test_cdi_dry_min(self):
        assert RULES.cdi_dry_min == 2

    def test_precip_1m_index_min(self):
        assert RULES.precip_1m_index_min == 2

    def test_soil_moisture_index_min(self):
        assert RULES.soil_moisture_index_min == 2

    def test_window_weeks(self):
        assert RULES.window_weeks == 52

    def test_horizon_days(self):
        assert RULES.horizon_days == 14

    def test_max_delta_days(self):
        assert RULES.max_delta_days == 5

    def test_fallback_min(self):
        assert RULES.fallback_min == 1


# ---------------------------------------------------------------------------
# settings.py re-exports still work (backward compatibility)
# ---------------------------------------------------------------------------

class TestSettingsReexports:
    def test_data_staleness_days_from_settings(self):
        from config.settings import DATA_STALENESS_DAYS
        assert DATA_STALENESS_DAYS == 14

    def test_indicator_columns_from_settings(self):
        from config.settings import INDICATOR_COLUMNS
        assert "cdi" in INDICATOR_COLUMNS
        assert len(INDICATOR_COLUMNS) == 10


# ---------------------------------------------------------------------------
# load_rules() can be called independently (not just as singleton)
# ---------------------------------------------------------------------------

class TestLoadRules:
    def test_load_rules_returns_rules_instance(self):
        r = load_rules()
        assert isinstance(r, Rules)

    def test_load_rules_fresh_copy(self):
        r1 = load_rules()
        r2 = load_rules()
        assert r1.staleness_days == r2.staleness_days

    def test_load_rules_missing_key_raises(self, tmp_path):
        bad_yaml = tmp_path / "rules.yaml"
        bad_yaml.write_text("data_quality:\n  staleness_days: 14\n", encoding="utf-8")
        import config.rules_loader as _rl
        orig = _rl._RULES_PATH
        _rl._RULES_PATH = bad_yaml
        try:
            with pytest.raises(KeyError):
                load_rules()
        finally:
            _rl._RULES_PATH = orig


# ---------------------------------------------------------------------------
# Behavioral: rules drive computation (spot-check pct_critical)
# ---------------------------------------------------------------------------

class TestRulesDriveComputation:
    def test_pct_critical_uses_cdi_critical_min(self):
        """Verify compute_pct_critical respects cdi_critical_min from rules."""
        import pandas as pd
        from src.aggregation.indicators import compute_pct_critical

        historic = pd.DataFrame({
            "drought_region_id": [99] * 4,
            "measured_at": pd.date_range("2025-01-01", periods=4, freq="W"),
            "cdi": [2, 3, 4, 1],
        })
        result = compute_pct_critical(historic, 99)
        # cdi_critical_min = 3 → weeks with cdi >= 3 are [3, 4] → 2 of 4
        assert result == pytest.approx(0.5)

    def test_pct_critical_explicit_n_weeks(self):
        """n_weeks parameter still overrides the default from rules."""
        import pandas as pd
        from src.aggregation.indicators import compute_pct_critical

        historic = pd.DataFrame({
            "drought_region_id": [99] * 4,
            "measured_at": pd.date_range("2025-01-01", periods=4, freq="W"),
            "cdi": [1, 1, 3, 4],
        })
        # Only last 2 weeks: [3, 4] → both critical → 100%
        result = compute_pct_critical(historic, 99, n_weeks=2)
        assert result == pytest.approx(1.0)
