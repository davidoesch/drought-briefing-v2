# tests/test_renderer.py
from pathlib import Path

from src.briefing.renderer import load_ruleset
from src.briefing.schemas import RulesetSchema


RULESET_PATH = Path(__file__).resolve().parent.parent / "data/ruleset/canton-bulletin.yaml"


def test_load_ruleset_returns_schema_instance():
    ruleset = load_ruleset(RULESET_PATH)
    assert isinstance(ruleset, RulesetSchema)
    assert ruleset.id == "canton-bulletin"
    assert "warnkarte" in ruleset.data_sources
    assert "niederschlag" in ruleset.nomenclature.indicators
