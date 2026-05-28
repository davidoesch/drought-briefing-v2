# tests/test_renderer.py
from pathlib import Path

from src.briefing.renderer import load_ruleset, _handlebars_to_jinja2
from src.briefing.schemas import RulesetSchema


RULESET_PATH = Path(__file__).resolve().parent.parent / "data/ruleset/canton-bulletin.yaml"


def test_load_ruleset_returns_schema_instance():
    ruleset = load_ruleset(RULESET_PATH)
    assert isinstance(ruleset, RulesetSchema)
    assert ruleset.id == "canton-bulletin"
    assert "warnkarte" in ruleset.data_sources
    assert "niederschlag" in ruleset.nomenclature.indicators


def test_handlebars_each_block_converted():
    src = "{{#each items}}- {{ this.name }}\n{{/each}}"
    out = _handlebars_to_jinja2(src)
    assert "{% for item in items %}" in out
    assert "{{ item.name }}" in out
    assert "{% endfor %}" in out


def test_handlebars_no_each_unchanged():
    src = "Hello {{ canton.canton_name_de }}."
    assert _handlebars_to_jinja2(src) == src
