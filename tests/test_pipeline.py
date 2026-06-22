"""
tests/test_pipeline.py

Phase 8 — Full System Validation

End-to-end pipeline validation covering all four MIGRATION_PLAN Phase 8 tasks:
  1. Full pipeline integration: aggregate → validate → generate_site
     (includes "multiple historical days" via determinism / idempotency checks)
  2. All regions: all 38 warning regions produce schema-valid outputs
  3. All indicators: every field is within its documented valid range
  4. Multilingual outputs: DE and FR briefings are correct and distinct
  Acceptance criteria:
  * zero functional regression
  * full automation working
  * production deployment ready (deterministic, schema-valid, bilingual)
"""
from __future__ import annotations

import copy
import importlib.util
import json
import sys
from pathlib import Path

import jsonschema
import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


# ---------------------------------------------------------------------------
# Script loading helpers
# ---------------------------------------------------------------------------

def _load_script(name: str):
    spec = importlib.util.spec_from_file_location(
        f"scripts_{name}", _REPO_ROOT / "scripts" / f"{name}.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_agg = _load_script("aggregate")
_val = _load_script("validate")
_site_mod = _load_script("generate_site")

run_aggregation = _agg.run_aggregation
_to_json = _agg._to_json
run_validation = _val.run_validation
generate_site = _site_mod.generate_site

from src.aggregation.canton import compute_canton_report
from src.aggregation.regional import compute_region_report
from src.briefing.renderer import load_ruleset, render_briefing
from src.data import vhi_client as _vhi_client
from src.data import warnkarte_client as _warnkarte_client
from src.data.fixture_loader import load as load_fixture
from config.rules_loader import RULES
from config.settings import CANTON_TO_REGIONS, REGION_NAMES_DE

RULESET_PATH = _REPO_ROOT / "data" / "ruleset" / "canton-bulletin.yaml"
SCHEMAS_DIR = _REPO_ROOT / "config" / "schemas"

_BERN_REGION_IDS: list[int] = [33, 34, 35, 37, 38, 41]
_TOTAL_REGIONS: int = len(REGION_NAMES_DE)    # 38
_TOTAL_CANTONS: int = len(CANTON_TO_REGIONS)  # 26


# ---------------------------------------------------------------------------
# Module-scoped shared fixtures (computed once per test run)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def fixture_bundle():
    return load_fixture()


@pytest.fixture(scope="module")
def warnkarte_bern():
    return _warnkarte_client._load_from_fixture(_BERN_REGION_IDS)


@pytest.fixture(scope="module")
def vhi_bern():
    return _vhi_client._load_from_fixture(_BERN_REGION_IDS)


@pytest.fixture(scope="module")
def all_bern_reports(fixture_bundle, warnkarte_bern, vhi_bern):
    """Dict[region_id → RegionReport] for all six Bern fixture regions."""
    return {
        rid: compute_region_report(rid, fixture_bundle, warnkarte_bern.get(rid), vhi_bern.get(rid))
        for rid in _BERN_REGION_IDS
    }


@pytest.fixture(scope="module")
def canton_2_report(fixture_bundle, warnkarte_bern, vhi_bern):
    """CantonReport for Bern computed with fixture data."""
    orig = _vhi_client.fetch_for_regions
    _vhi_client.fetch_for_regions = lambda rids: {r: vhi_bern[r] for r in rids if r in vhi_bern}
    try:
        return compute_canton_report(2, fixture_bundle, warnkarte_bern)
    finally:
        _vhi_client.fetch_for_regions = orig


@pytest.fixture(scope="module")
def ruleset():
    return load_ruleset(RULESET_PATH)


@pytest.fixture(scope="module")
def doc_de(canton_2_report, ruleset):
    return render_briefing(canton_2_report, ruleset, locale="de")


@pytest.fixture(scope="module")
def doc_fr(canton_2_report, ruleset):
    return render_briefing(canton_2_report, ruleset, locale="fr")


@pytest.fixture(scope="module")
def region_schema():
    return json.loads((SCHEMAS_DIR / "region.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def canton_schema():
    return json.loads((SCHEMAS_DIR / "canton.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def full_pipeline(tmp_path_factory):
    """
    Run the complete pipeline (with fixture fallback) once per test session.
    Returns a dict with 'processed' and 'site' Path objects.
    """
    base = tmp_path_factory.mktemp("full_pipeline")
    raw_dir = base / "raw"           # intentionally absent → fixture fallback
    processed_dir = base / "processed"
    site_dir = base / "site"
    run_aggregation(raw_dir, processed_dir)
    generate_site(processed_dir, RULESET_PATH, site_dir)
    return {"processed": processed_dir, "site": site_dir}


# ---------------------------------------------------------------------------
# 1. Full pipeline integration
# ---------------------------------------------------------------------------

class TestFullPipelineIntegration:
    """
    Aggregate → validate → generate_site: all expected outputs are present
    and the pipeline is idempotent across repeated runs (multiple historical days).
    """

    def test_aggregate_writes_all_region_jsons(self, full_pipeline):
        files = list((full_pipeline["processed"] / "warning_regions").glob("*.json"))
        assert len(files) == _TOTAL_REGIONS

    def test_aggregate_writes_all_canton_jsons(self, full_pipeline):
        files = list((full_pipeline["processed"] / "cantons").glob("*.json"))
        assert len(files) == _TOTAL_CANTONS

    def test_validate_finds_no_errors_on_pipeline_output(self, full_pipeline):
        errors = run_validation(full_pipeline["processed"])
        assert errors == [], f"Unexpected validation errors: {errors}"

    def test_site_index_html_exists(self, full_pipeline):
        assert (full_pipeline["site"] / "index.html").exists()

    def test_site_has_canton_page_for_every_canton(self, full_pipeline):
        pages = list((full_pipeline["site"] / "canton").glob("*/index.html"))
        assert len(pages) == _TOTAL_CANTONS

    def test_site_assets_exist(self, full_pipeline):
        assert (full_pipeline["site"] / "assets" / "style.css").exists()
        assert (full_pipeline["site"] / "assets" / "app.js").exists()

    def test_site_data_json_copied_for_all_cantons(self, full_pipeline):
        copies = list((full_pipeline["site"] / "data" / "cantons").glob("*.json"))
        assert len(copies) == _TOTAL_CANTONS

    def test_pipeline_is_idempotent_for_region_output(self, tmp_path):
        """
        Running the pipeline twice on identical inputs (fixture fallback)
        produces byte-identical JSON — equivalent to re-running on the same
        historical day.
        """
        run_aggregation(tmp_path / "raw", tmp_path / "proc1")
        run_aggregation(tmp_path / "raw", tmp_path / "proc2")
        for f1 in sorted((tmp_path / "proc1" / "warning_regions").glob("*.json")):
            f2 = tmp_path / "proc2" / "warning_regions" / f1.name
            assert json.loads(f1.read_text()) == json.loads(f2.read_text()), (
                f"{f1.name} differs between runs"
            )

    def test_pipeline_is_idempotent_for_canton_output(self, tmp_path):
        """Same as above for canton-level outputs."""
        run_aggregation(tmp_path / "raw", tmp_path / "proc1")
        run_aggregation(tmp_path / "raw", tmp_path / "proc2")
        for f1 in sorted((tmp_path / "proc1" / "cantons").glob("*.json")):
            f2 = tmp_path / "proc2" / "cantons" / f1.name
            assert json.loads(f1.read_text()) == json.loads(f2.read_text()), (
                f"{f1.name} differs between runs"
            )

    def test_output_schema_valid_for_different_timestamp(self, full_pipeline, canton_schema):
        """
        A processed canton JSON with a different data_timestamp (simulating a
        different historical day) still satisfies the schema — the schema is
        date-agnostic by design.
        """
        sample_path = next((full_pipeline["processed"] / "cantons").glob("*.json"))
        original = json.loads(sample_path.read_text(encoding="utf-8"))
        historical = copy.deepcopy(original)
        historical["data_timestamp"] = "2025-06-15T00:00:00"
        for region in historical["regions"]:
            region["data_timestamp"] = "2025-06-15T00:00:00"
        jsonschema.validate(historical, canton_schema)  # must not raise


# ---------------------------------------------------------------------------
# 2. All regions
# ---------------------------------------------------------------------------

class TestAllRegions:
    """All 38 pipeline-generated region outputs are schema-valid; all six
    fixture-supported regions satisfy field-level constraints."""

    def test_all_pipeline_regions_pass_schema(self, full_pipeline):
        """The validation step must report zero errors for all 38 regions."""
        errors = run_validation(full_pipeline["processed"])
        assert errors == [], f"Schema violations in region outputs: {errors}"

    def test_all_bern_regions_pass_schema(self, all_bern_reports, region_schema):
        for rid, report in all_bern_reports.items():
            data = json.loads(_to_json(report))
            try:
                jsonschema.validate(data, region_schema)
            except jsonschema.ValidationError as exc:
                pytest.fail(f"Region {rid}: {exc.message}")

    def test_all_bern_regions_have_valid_cdi(self, all_bern_reports):
        for rid, report in all_bern_reports.items():
            assert 0 <= report.cdi <= 5, f"Region {rid}: CDI={report.cdi}"

    def test_all_bern_regions_have_valid_warnlevel(self, all_bern_reports):
        for rid, report in all_bern_reports.items():
            assert 1 <= report.warnlevel <= 5, f"Region {rid}: warnlevel={report.warnlevel}"

    def test_all_bern_regions_have_valid_cdi_trend(self, all_bern_reports):
        for rid, report in all_bern_reports.items():
            assert report.cdi_trend in (-1, 0, 1), f"Region {rid}: cdi_trend={report.cdi_trend}"

    def test_all_bern_regions_have_non_empty_name(self, all_bern_reports):
        for rid, report in all_bern_reports.items():
            assert report.region_name_de, f"Region {rid}: empty region_name_de"

    def test_all_bern_regions_have_quality_status(self, all_bern_reports):
        for rid, report in all_bern_reports.items():
            assert report.quality.overall in {"ok", "warning", "error"}, (
                f"Region {rid}: quality.overall={report.quality.overall!r}"
            )

    def test_all_bern_regions_have_valid_source(self, all_bern_reports):
        for rid, report in all_bern_reports.items():
            assert report.source in ("api", "fixture"), (
                f"Region {rid}: source={report.source!r}"
            )


# ---------------------------------------------------------------------------
# 3. All indicators
# ---------------------------------------------------------------------------

class TestAllIndicators:
    """Every indicator field for a representative region is within range."""

    @pytest.fixture(scope="class")
    def r34(self, fixture_bundle, warnkarte_bern, vhi_bern):
        return compute_region_report(34, fixture_bundle, warnkarte_bern.get(34), vhi_bern.get(34))

    def test_cdi_is_int_in_range(self, r34):
        assert isinstance(r34.cdi, int) and 0 <= r34.cdi <= 5

    def test_cdi_trend_is_valid_enum(self, r34):
        assert r34.cdi_trend in (-1, 0, 1)

    def test_pct_critical_is_fraction(self, r34):
        assert 0.0 <= r34.pct_critical <= 1.0

    def test_spi_3m_percentile_in_range(self, r34):
        assert 0 <= r34.spi_3m_percentile <= 100

    def test_precip_1m_index_in_range(self, r34):
        assert 1 <= r34.precip_1m_index <= 5

    def test_soil_moisture_index_in_range(self, r34):
        assert 1 <= r34.soil_moisture_index <= 5

    def test_hydro_index_in_range(self, r34):
        assert 1 <= r34.hydro_index <= 5

    def test_warnlevel_in_range(self, r34):
        assert 1 <= r34.warnlevel <= 5

    def test_spi_3m_is_float(self, r34):
        assert isinstance(r34.spi_3m, float)

    def test_vhi_is_float(self, r34):
        assert isinstance(r34.vhi, float)

    def test_soil_moisture_pct_is_float(self, r34):
        assert isinstance(r34.soil_moisture_pct, float)

    def test_discharge_n_low_lte_n_total(self, r34):
        assert r34.discharge.n_low <= r34.discharge.n_total

    def test_discharge_n_very_low_lte_n_low(self, r34):
        assert r34.discharge.n_very_low <= r34.discharge.n_low

    def test_discharge_pct_low_in_range(self, r34):
        assert 0 <= r34.discharge.pct_low <= 100

    def test_discharge_pct_low_zero_when_no_stations(self, r34):
        if r34.discharge.n_total == 0:
            assert r34.discharge.pct_low == 0

    def test_data_timestamp_is_datetime(self, r34):
        from datetime import datetime
        assert isinstance(r34.data_timestamp, datetime)

    def test_quality_coverage_pct_in_range(self, r34):
        assert 0.0 <= r34.quality.coverage_pct <= 1.0

    def test_quality_data_age_non_negative(self, r34):
        assert r34.quality.data_age_days >= 0


# ---------------------------------------------------------------------------
# 4. Canton-level indicators
# ---------------------------------------------------------------------------

class TestCantonIndicators:
    """Canton aggregated fields satisfy invariants derived from their regions."""

    def test_max_warnlevel_equals_max_of_regions(self, canton_2_report):
        expected = max(r.warnlevel for r in canton_2_report.regions)
        assert canton_2_report.max_warnlevel == expected

    def test_n_regions_dry_matches_rule_threshold(self, canton_2_report):
        expected = sum(1 for r in canton_2_report.regions if r.cdi >= RULES.cdi_dry_min)
        assert canton_2_report.n_regions_dry == expected

    def test_region_count_matches_canton_definition(self, canton_2_report):
        assert len(canton_2_report.regions) == len(CANTON_TO_REGIONS[2])

    def test_precip_index_counts_sum_to_total(self, canton_2_report):
        total = sum(canton_2_report.n_regions_by_precip_index.values())
        assert total == len(canton_2_report.regions)

    def test_soil_moisture_index_counts_sum_to_total(self, canton_2_report):
        total = sum(canton_2_report.n_regions_by_soil_moisture_index.values())
        assert total == len(canton_2_report.regions)

    def test_hydro_index_counts_sum_to_total(self, canton_2_report):
        total = sum(canton_2_report.n_regions_by_hydro_index.values())
        assert total == len(canton_2_report.regions)

    def test_canton_discharge_consistency(self, canton_2_report):
        assert canton_2_report.discharge.n_low <= canton_2_report.discharge.n_total
        assert canton_2_report.discharge.n_very_low <= canton_2_report.discharge.n_low

    def test_cdi_min_dry_lte_cdi_max_dry(self, canton_2_report):
        if canton_2_report.cdi_min_dry is not None:
            assert canton_2_report.cdi_min_dry <= canton_2_report.cdi_max_dry

    def test_max_warnlevel_in_range(self, canton_2_report):
        assert 1 <= canton_2_report.max_warnlevel <= 5

    def test_n_regions_with_precip_deficit_consistent(self, canton_2_report):
        expected = sum(
            1 for r in canton_2_report.regions if r.precip_1m_index >= RULES.precip_1m_index_min
        )
        assert canton_2_report.n_regions_with_precip_deficit == expected

    def test_n_regions_with_soil_moisture_deficit_consistent(self, canton_2_report):
        expected = sum(
            1 for r in canton_2_report.regions
            if r.soil_moisture_index >= RULES.soil_moisture_index_min
        )
        assert canton_2_report.n_regions_with_soil_moisture_deficit == expected


# ---------------------------------------------------------------------------
# 5. Multilingual outputs
# ---------------------------------------------------------------------------

class TestMultilingualOutputs:
    """DE and FR outputs are non-empty, locale-distinct, and appear in the site."""

    def test_de_briefing_has_sections(self, doc_de):
        assert doc_de.sections

    def test_fr_briefing_has_sections(self, doc_fr):
        assert doc_fr.sections

    def test_both_locales_have_same_section_ids(self, doc_de, doc_fr):
        assert set(doc_de.sections) == set(doc_fr.sections)

    def test_de_headline_non_empty(self, doc_de):
        assert doc_de.lead_headline.strip()

    def test_fr_headline_non_empty(self, doc_fr):
        assert doc_fr.lead_headline.strip()

    def test_de_and_fr_headlines_differ(self, doc_de, doc_fr):
        assert doc_de.lead_headline != doc_fr.lead_headline

    def test_de_sections_non_empty(self, doc_de):
        for sec_id, text in doc_de.sections.items():
            assert text.strip(), f"DE section '{sec_id}' is empty"

    def test_fr_sections_non_empty(self, doc_fr):
        for sec_id, text in doc_fr.sections.items():
            assert text.strip(), f"FR section '{sec_id}' is empty"

    def test_de_and_fr_section_content_differs(self, doc_de, doc_fr):
        """At least one section must differ between locales."""
        any_differ = any(doc_de.sections[k] != doc_fr.sections[k] for k in doc_de.sections)
        assert any_differ, "DE and FR section content is identical — locale rendering may be broken"

    def test_canton_page_contains_lang_de_class(self, full_pipeline):
        content = (full_pipeline["site"] / "canton" / "2" / "index.html").read_text("utf-8")
        assert "lang-de" in content

    def test_canton_page_contains_lang_fr_class(self, full_pipeline):
        content = (full_pipeline["site"] / "canton" / "2" / "index.html").read_text("utf-8")
        assert "lang-fr" in content

    def test_canton_page_contains_german_canton_name(self, full_pipeline, canton_2_report):
        content = (full_pipeline["site"] / "canton" / "2" / "index.html").read_text("utf-8")
        assert canton_2_report.canton_name_de in content

    def test_canton_page_contains_french_canton_name(self, full_pipeline, canton_2_report):
        content = (full_pipeline["site"] / "canton" / "2" / "index.html").read_text("utf-8")
        assert canton_2_report.canton_name_fr in content

    def test_canton_page_has_language_toggle_buttons(self, full_pipeline):
        content = (full_pipeline["site"] / "canton" / "2" / "index.html").read_text("utf-8")
        assert 'data-lang="de"' in content
        assert 'data-lang="fr"' in content

    def test_index_page_has_both_locale_labels(self, full_pipeline):
        content = (full_pipeline["site"] / "index.html").read_text("utf-8")
        assert "lang-de" in content
        assert "lang-fr" in content


# ---------------------------------------------------------------------------
# 6. Determinism (idempotent execution)
# ---------------------------------------------------------------------------

class TestDeterminism:
    """Same fixture inputs always produce byte-identical JSON and HTML."""

    def test_region_report_json_is_deterministic(self, fixture_bundle, warnkarte_bern, vhi_bern):
        r1 = compute_region_report(34, fixture_bundle, warnkarte_bern.get(34), vhi_bern.get(34))
        r2 = compute_region_report(34, fixture_bundle, warnkarte_bern.get(34), vhi_bern.get(34))
        assert _to_json(r1) == _to_json(r2)

    def test_all_bern_region_reports_are_deterministic(
        self, fixture_bundle, warnkarte_bern, vhi_bern
    ):
        for rid in _BERN_REGION_IDS:
            r1 = compute_region_report(rid, fixture_bundle, warnkarte_bern.get(rid), vhi_bern.get(rid))
            r2 = compute_region_report(rid, fixture_bundle, warnkarte_bern.get(rid), vhi_bern.get(rid))
            assert _to_json(r1) == _to_json(r2), f"Region {rid} is not deterministic"

    def test_canton_report_json_is_deterministic(self, fixture_bundle, warnkarte_bern, vhi_bern):
        def _build():
            orig = _vhi_client.fetch_for_regions
            _vhi_client.fetch_for_regions = lambda rids: {r: vhi_bern[r] for r in rids if r in vhi_bern}
            try:
                return compute_canton_report(2, fixture_bundle, warnkarte_bern)
            finally:
                _vhi_client.fetch_for_regions = orig

        assert _to_json(_build()) == _to_json(_build())

    def test_briefing_render_is_deterministic(self, canton_2_report, ruleset):
        d1 = render_briefing(canton_2_report, ruleset, locale="de")
        d2 = render_briefing(canton_2_report, ruleset, locale="de")
        assert d1.lead_headline == d2.lead_headline
        assert d1.sections == d2.sections


# ---------------------------------------------------------------------------
# 7. Regression invariants
# ---------------------------------------------------------------------------

class TestRegressionInvariants:
    """Scientific constraints and business rules that the pipeline must uphold."""

    def test_warnlevel_never_zero_across_all_pipeline_regions(self, full_pipeline):
        for path in (full_pipeline["processed"] / "warning_regions").glob("*.json"):
            d = json.loads(path.read_text(encoding="utf-8"))
            assert d["warnlevel"] >= 1, f"{path.name}: warnlevel=0 violates fallback_min rule"

    def test_warnlevel_never_zero_across_all_bern_fixture_regions(self, all_bern_reports):
        for rid, report in all_bern_reports.items():
            assert report.warnlevel >= 1, f"Region {rid}: warnlevel below minimum of 1"

    def test_pct_critical_consistent_with_historic_data(
        self, fixture_bundle, warnkarte_bern, vhi_bern
    ):
        """pct_critical > 0 only when the historic data actually contains critical weeks."""
        report = compute_region_report(34, fixture_bundle, warnkarte_bern.get(34), vhi_bern.get(34))
        if report.pct_critical > 0:
            hist = fixture_bundle.historic_df[fixture_bundle.historic_df["drought_region_id"] == 34]
            n_critical = (hist["cdi"] >= RULES.cdi_critical_min).sum()
            assert n_critical > 0, (
                "pct_critical > 0 but no critical CDI weeks found in historic data"
            )

    def test_stale_flag_consistent_with_staleness_threshold(self, all_bern_reports):
        """is_stale must be True whenever data_age_days exceeds the configured threshold."""
        for rid, report in all_bern_reports.items():
            if report.quality.data_age_days > RULES.staleness_days:
                assert report.quality.is_stale, (
                    f"Region {rid}: data_age_days={report.quality.data_age_days} "
                    f"> staleness_days={RULES.staleness_days} but is_stale=False"
                )

    def test_coverage_pct_in_valid_range_for_all_bern_regions(self, all_bern_reports):
        for rid, report in all_bern_reports.items():
            assert 0.0 <= report.quality.coverage_pct <= 1.0, (
                f"Region {rid}: coverage_pct={report.quality.coverage_pct}"
            )

    def test_data_age_non_negative_for_all_bern_regions(self, all_bern_reports):
        for rid, report in all_bern_reports.items():
            assert report.quality.data_age_days >= 0, (
                f"Region {rid}: data_age_days is negative"
            )

    def test_canton_max_warnlevel_is_max_of_region_warnlevels(self, canton_2_report):
        expected = max(r.warnlevel for r in canton_2_report.regions)
        assert canton_2_report.max_warnlevel == expected

    def test_no_jinja2_syntax_in_any_site_page(self, full_pipeline):
        """No Jinja2 template syntax must leak into any generated HTML page."""
        for html_path in (full_pipeline["site"]).rglob("*.html"):
            content = html_path.read_text(encoding="utf-8")
            assert "{{" not in content, f"{html_path.name}: Jinja2 syntax leaked"
            assert "{%" not in content, f"{html_path.name}: Jinja2 syntax leaked"

    def test_all_canton_pages_reference_assets(self, full_pipeline):
        """Every canton page must link to style.css and app.js."""
        for html_path in (full_pipeline["site"] / "canton").rglob("index.html"):
            content = html_path.read_text(encoding="utf-8")
            assert "style.css" in content, f"{html_path}: missing style.css link"
            assert "app.js" in content, f"{html_path}: missing app.js link"
