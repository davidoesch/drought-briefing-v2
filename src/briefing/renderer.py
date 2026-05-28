# src/briefing/renderer.py
from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Literal

import yaml
from jinja2 import BaseLoader, Environment, StrictUndefined

from src.briefing.schemas import RulesetSchema
from src.models import BriefingDocument, CantonReport, MapSpec

_EACH_OPEN = re.compile(r"\{\{#each\s+([^\s}]+)\s*\}\}")
_EACH_CLOSE = re.compile(r"\{\{/each\}\}")
_THIS_FIELD = re.compile(r"\{\{\s*this\.([^\s}]+)\s*\}\}")
_THIS_BARE = re.compile(r"\{\{\s*this\s*\}\}")
# Also replaces `this.field` inside other expressions (e.g. subscripts like [this.field])
_THIS_INPLACE = re.compile(r"\bthis\.")


def _handlebars_to_jinja2(src: str) -> str:
    src = _EACH_OPEN.sub(r"{% for item in \1 %}", src)
    src = _EACH_CLOSE.sub("{% endfor %}", src)
    src = _THIS_FIELD.sub(r"{{ item.\1 }}", src)
    src = _THIS_BARE.sub(r"{{ item }}", src)
    # Replace any remaining `this.` references inside Jinja2 expressions
    src = _THIS_INPLACE.sub("item.", src)
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


def _format_date(value: datetime | str, pattern: str) -> str:
    if isinstance(value, str):
        value = datetime.fromisoformat(value)
    mapping = {
        "DD.MM.YYYY": value.strftime("%d.%m.%Y"),
        "YYYY-MM-DD": value.strftime("%Y-%m-%d"),
    }
    return mapping.get(pattern, value.strftime(pattern))


def _make_trend_resolver(trend_spec, locale: str):
    def trend(delta, key):
        spec = trend_spec[key]
        if abs(delta) <= spec.stable_tolerance:
            return spec.stable[locale]
        return (spec.increase if delta > 0 else spec.decrease)[locale]
    return trend


def render_briefing(
    canton: CantonReport,
    ruleset: RulesetSchema,
    locale: Literal["de", "fr"] = "de",
) -> BriefingDocument:
    env = Environment(
        loader=BaseLoader(),
        undefined=StrictUndefined,
        autoescape=False,
    )
    env.filters["format_date"] = _format_date
    env.globals["format_date"] = _format_date
    env.globals["trend"] = _make_trend_resolver(ruleset.trend, locale)
    env.globals["nomenclature"] = ruleset.nomenclature.indicators
    env.globals["handlungsempfehlungen"] = ruleset.handlungsempfehlungen
    env.globals["canton"] = canton
    # Expose data_sources and references as lists so Handlebars-style each loops work
    env.globals["data_sources"] = list(ruleset.data_sources.values())
    env.globals["references"] = list(ruleset.references.values())

    sections: dict[str, str] = {}
    for sec in ruleset.sections:
        if isinstance(sec.template, str):
            tmpl_src = sec.template
        else:
            tmpl_src = sec.template.get(locale, sec.template.get("de", ""))
        tmpl_src = _handlebars_to_jinja2(tmpl_src)
        sections[sec.id] = env.from_string(tmpl_src).render().strip()

    # Lead
    lead = ruleset.lead.warnstufe
    headline = env.from_string(_handlebars_to_jinja2(lead.headline[locale])).render()
    meta = env.from_string(_handlebars_to_jinja2(lead.meta[locale])).render()
    lead_maps = [
        MapSpec(
            id=m.id,
            title_de=m.title.get("de", ""),
            title_fr=m.title.get("fr", ""),
            source=m.source,
            style=m.style,
        )
        for m in lead.maps
    ]

    return BriefingDocument(
        sections=sections,
        report=canton,
        locale=locale,
        generated_at=datetime.now(),
        lead_maps=lead_maps,
        lead_headline=headline,
        lead_meta=meta,
    )
