# src/briefing/renderer.py
from __future__ import annotations

import re
from pathlib import Path

import yaml

from src.briefing.schemas import RulesetSchema

_EACH_OPEN = re.compile(r"\{\{#each\s+([^\s}]+)\s*\}\}")
_EACH_CLOSE = re.compile(r"\{\{/each\}\}")
_THIS_FIELD = re.compile(r"\{\{\s*this\.([^\s}]+)\s*\}\}")


def _handlebars_to_jinja2(src: str) -> str:
    src = _EACH_OPEN.sub(r"{% for item in \1 %}", src)
    src = _EACH_CLOSE.sub("{% endfor %}", src)
    src = _THIS_FIELD.sub(r"{{ item.\1 }}", src)
    return src


def load_ruleset(path: Path) -> RulesetSchema:
    """Load YAML, validate via Pydantic, return the schema object."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(raw, dict):
        raise ValueError(f"Expected a YAML mapping at the top level, got {type(raw).__name__}")

    # NomenclatureSpec wraps the raw mapping under an `indicators` key for type clarity.
    if "nomenclature" in raw and "indicators" not in raw["nomenclature"]:
        raw["nomenclature"] = {"indicators": raw["nomenclature"]}

    return RulesetSchema.model_validate(raw)
