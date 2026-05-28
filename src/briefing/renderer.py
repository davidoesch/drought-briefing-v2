# src/briefing/renderer.py
from __future__ import annotations

from pathlib import Path

import yaml

from src.briefing.schemas import RulesetSchema


def load_ruleset(path: Path) -> RulesetSchema:
    """Load YAML, validate via Pydantic, return the schema object."""
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))

    if not isinstance(raw, dict):
        raise ValueError(f"Expected a YAML mapping at the top level, got {type(raw).__name__}")

    # NomenclatureSpec wraps the raw mapping under an `indicators` key for type clarity.
    if "nomenclature" in raw and "indicators" not in raw["nomenclature"]:
        raw["nomenclature"] = {"indicators": raw["nomenclature"]}

    return RulesetSchema.model_validate(raw)
