"""
scripts/validate.py

Purpose : Validate all files in data/processed/ against the JSON Schema
          contract defined in config/schemas/.
Inputs  : data/processed/warning_regions/*.json  – per-region outputs
          data/processed/cantons/*.json           – per-canton outputs
          config/schemas/region.json              – RegionReport schema
          config/schemas/canton.json              – CantonReport schema
Outputs : Validation report on stdout; exits 1 if any file fails validation.
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import jsonschema

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

SCHEMAS_DIR = _REPO_ROOT / "config" / "schemas"
PROCESSED_DIR = _REPO_ROOT / "data" / "processed"

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _load_schema(name: str) -> dict:
    path = SCHEMAS_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))


def _validate(data: dict, schema: dict, label: str, errors: list[str]) -> bool:
    """Validate data against schema; append error messages to errors list."""
    try:
        jsonschema.validate(data, schema)
        return True
    except jsonschema.ValidationError as exc:
        errors.append(f"{label}: {exc.message} (at {list(exc.path)})")
        return False
    except jsonschema.SchemaError as exc:
        errors.append(f"{label}: schema error — {exc.message}")
        return False


def validate_regions(
    processed_dir: Path,
    region_schema: dict,
) -> list[str]:
    """Validate all warning_regions/*.json; return list of error messages."""
    errors: list[str] = []
    region_dir = processed_dir / "warning_regions"
    if not region_dir.exists():
        log.warning("warning_regions/ not found in %s — skipping", processed_dir)
        return errors

    files = sorted(region_dir.glob("*.json"))
    if not files:
        log.warning("No region JSON files found in %s", region_dir)
        return errors

    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        _validate(data, region_schema, path.name, errors)

    return errors


def validate_cantons(
    processed_dir: Path,
    canton_schema: dict,
    region_schema: dict,
) -> list[str]:
    """Validate all cantons/*.json; return list of error messages."""
    errors: list[str] = []
    canton_dir = processed_dir / "cantons"
    if not canton_dir.exists():
        log.warning("cantons/ not found in %s — skipping", processed_dir)
        return errors

    files = sorted(canton_dir.glob("*.json"))
    if not files:
        log.warning("No canton JSON files found in %s", canton_dir)
        return errors

    for path in files:
        data = json.loads(path.read_text(encoding="utf-8"))
        _validate(data, canton_schema, path.name, errors)

        # Validate each embedded region report against the region schema.
        for i, region_data in enumerate(data.get("regions", [])):
            region_id = region_data.get("region_id", i)
            _validate(
                region_data,
                region_schema,
                f"{path.name}:regions[{i}] (id={region_id})",
                errors,
            )

    return errors


def run_validation(processed_dir: Path) -> list[str]:
    """Load schemas and validate all processed outputs. Return all error messages."""
    region_schema = _load_schema("region.json")
    canton_schema = _load_schema("canton.json")

    errors: list[str] = []
    errors.extend(validate_regions(processed_dir, region_schema))
    errors.extend(validate_cantons(processed_dir, canton_schema, region_schema))
    return errors


def main() -> None:
    processed_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else PROCESSED_DIR

    if not processed_dir.exists():
        log.error("Processed directory not found: %s — run scripts/aggregate.py first.", processed_dir)
        sys.exit(1)

    log.info("Validating %s ...", processed_dir)
    errors = run_validation(processed_dir)

    if errors:
        log.error("%d validation error(s) found:", len(errors))
        for err in errors:
            log.error("  %s", err)
        sys.exit(1)

    log.info("All processed JSON files are valid.")


if __name__ == "__main__":
    main()
