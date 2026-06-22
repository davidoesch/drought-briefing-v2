"""
scripts/download.py

Purpose : Download all raw source datasets and write them to data/raw/.
Inputs  : BGDI STAC API, geo.admin.ch Warnkarte REST API, SwissEO VHI endpoint.
Outputs : data/raw/
            current.zip    – weekly current region & station data + forecast
            historic.zip   – weekly historic region data
            reference.zip  – reference thresholds (regions + stations)
            warnkarte.json – BAFU warning levels per region (raw API responses)
            vhi.csv        – vegetation health index per warning region
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

import requests

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from config.settings import REGION_NAMES_DE, STAC_BASE_URL, STAC_COLLECTION, VHI_URL

RAW_DIR = _REPO_ROOT / "data" / "raw"

_WARNKARTE_URL = (
    "https://api3.geo.admin.ch/rest/services/api/MapServer"
    "/ch.bafu.trockenheitswarnkarte/{rid}"
)
_TIMEOUT = 10
_DOWNLOAD_TIMEOUT = 60

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)


def _stac_items(items_url: str) -> list[dict]:
    items: list[dict] = []
    url: str | None = items_url
    params: dict | None = {"limit": 100}
    while url:
        r = requests.get(url, params=params, timeout=_TIMEOUT)
        r.raise_for_status()
        data = r.json()
        items.extend(data.get("features", []))
        url = next(
            (link["href"] for link in data.get("links", []) if link.get("rel") == "next"),
            None,
        )
        params = None
    return items


def _asset_href(items: list[dict], keyword: str) -> str:
    for item in items:
        for key, asset in item.get("assets", {}).items():
            if keyword in key:
                href = asset.get("href", "")
                if href:
                    return href
    raise RuntimeError(f"No STAC asset containing '{keyword}'")


def download_stac(raw_dir: Path) -> None:
    log.info("Querying STAC collection %s ...", STAC_COLLECTION)
    items = _stac_items(f"{STAC_BASE_URL}/collections/{STAC_COLLECTION}/items")
    if not items:
        raise RuntimeError("STAC collection returned no items")
    for keyword, filename in [
        ("current",   "current.zip"),
        ("historic",  "historic.zip"),
        ("reference", "reference.zip"),
    ]:
        url = _asset_href(items, keyword)
        log.info("Downloading %s ...", filename)
        r = requests.get(url, timeout=_DOWNLOAD_TIMEOUT)
        r.raise_for_status()
        (raw_dir / filename).write_bytes(r.content)
        log.info("  Saved %s (%d KB)", filename, len(r.content) // 1024)


def download_warnkarte(raw_dir: Path) -> None:
    region_ids = sorted(REGION_NAMES_DE.keys())
    log.info("Downloading Warnkarte for %d regions ...", len(region_ids))
    raw: dict[str, object] = {}
    for rid in region_ids:
        r = requests.get(_WARNKARTE_URL.format(rid=rid), timeout=_TIMEOUT)
        r.raise_for_status()
        raw[str(rid)] = r.json()
    (raw_dir / "warnkarte.json").write_text(
        json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    log.info("  Saved warnkarte.json (%d regions)", len(raw))


def download_vhi(raw_dir: Path) -> None:
    log.info("Downloading VHI CSV ...")
    r = requests.get(VHI_URL, timeout=_TIMEOUT)
    r.raise_for_status()
    (raw_dir / "vhi.csv").write_bytes(r.content)
    log.info("  Saved vhi.csv (%d KB)", len(r.content) // 1024)


def main() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    errors: list[str] = []
    for name, fn in [
        ("STAC datasets", lambda: download_stac(RAW_DIR)),
        ("Warnkarte",     lambda: download_warnkarte(RAW_DIR)),
        ("VHI",           lambda: download_vhi(RAW_DIR)),
    ]:
        try:
            fn()
        except Exception as exc:
            log.error("%s failed: %s", name, exc)
            errors.append(name)
    if errors:
        log.error("Failed sources: %s", ", ".join(errors))
        sys.exit(1)
    log.info("All raw data downloaded to %s", RAW_DIR)


if __name__ == "__main__":
    main()
