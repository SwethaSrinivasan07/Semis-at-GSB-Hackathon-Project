"""
Distributor API — single entry point for component data.

Strategy: try live distributor APIs first (if keys present in environment),
fall back to the bundled mock dataset otherwise. Downstream modules
(risk_engine, substitution, report_generator) should only depend on the
return contract documented below, never on which source served the data.

Part record contract (same shape used everywhere downstream):
    {
        "mpn": str,
        "manufacturer": str,
        "category": str,                # e.g. "Transceiver", "ASIC/DSP"
        "description": str,
        "price_usd": float,
        "lead_time_weeks": int,
        "stock": int,
        "lifecycle": str,               # "Active" | "NRND" | "EOL" | "Obsolete"
        "fab_country": str,
        "package_country": str | None,
        "supplier_count": int,          # 1 = single source globally
        "alternates_available": bool,
        "datasheet_url": str,
        "rohs_compliant": bool,
        "notes": str,
        "last_updated": str,            # ISO date
        "_source": str,                 # "mock" | "digikey" | "mouser" | "arrow"
    }
"""

from __future__ import annotations

import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

log = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MOCK_DATA_PATH = DATA_DIR / "mock_distributor_data.json"
GEO_RISK_PATH = DATA_DIR / "geo_risk_map.json"


@lru_cache(maxsize=1)
def _load_mock_dataset() -> dict[str, dict[str, Any]]:
    """Load mock parts into an mpn → record dict for O(1) lookups."""
    with MOCK_DATA_PATH.open("r", encoding="utf-8") as fh:
        payload = json.load(fh)
    return {p["mpn"]: p for p in payload["parts"]}


@lru_cache(maxsize=1)
def load_geo_risk() -> dict[str, Any]:
    """Return the geo risk map. Cached for the process lifetime."""
    with GEO_RISK_PATH.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def _get_live_clients() -> list[Any]:
    """
    Instantiate any distributor clients whose API keys are present in env.
    Returns clients in priority order (DigiKey, Mouser, Arrow).
    """
    from . import api_integrations as integrations

    clients: list[Any] = []
    if os.getenv("DIGIKEY_API_KEY"):
        clients.append(integrations.DigiKeyAPI(os.environ["DIGIKEY_API_KEY"]))
    if os.getenv("MOUSER_API_KEY"):
        clients.append(integrations.MouserAPI(os.environ["MOUSER_API_KEY"]))
    if os.getenv("ARROW_API_KEY"):
        clients.append(integrations.ArrowAPI(os.environ["ARROW_API_KEY"]))
    return clients


def search_part(mpn: str) -> dict[str, Any] | None:
    """
    Look up a part by manufacturer part number.

    Tries each live distributor in order; falls back to the mock dataset.
    Returns None if the part is unknown to every source.
    """
    mpn = mpn.strip()

    for client in _get_live_clients():
        try:
            record = client.search_part(mpn)
            if record:
                record["_source"] = client.source_name
                return record
        except Exception as exc:
            log.warning("Live lookup via %s failed for %s: %s", client.source_name, mpn, exc)

    mock = _load_mock_dataset().get(mpn)
    if mock:
        record = dict(mock)
        record["_source"] = "mock"
        return record

    return None


def get_pricing(mpn: str, qty: int) -> dict[str, Any]:
    """
    Return pricing for `qty` of `mpn`. Live distributor first, else compute
    from the mock unit price with a simple volume curve.
    """
    for client in _get_live_clients():
        try:
            quote = client.get_pricing(mpn, qty)
            if quote:
                quote["_source"] = client.source_name
                return quote
        except Exception as exc:
            log.warning("Live pricing via %s failed for %s: %s", client.source_name, mpn, exc)

    part = _load_mock_dataset().get(mpn.strip())
    if not part:
        return {"mpn": mpn, "qty": qty, "unit_price_usd": None, "total_usd": None, "_source": "none"}

    unit = float(part["price_usd"])
    # Toy volume curve: 1% off per 10x of qty over 1, capped at 30%.
    if qty > 1:
        import math

        discount = min(0.30, 0.01 * math.log10(qty) * 10)
        unit = round(unit * (1 - discount), 4)

    return {
        "mpn": mpn,
        "qty": qty,
        "unit_price_usd": unit,
        "total_usd": round(unit * qty, 2),
        "_source": "mock",
    }


def get_all_parts() -> list[dict[str, Any]]:
    """Return every part the mock dataset knows about. Used by demo_mode and tests."""
    return [dict(p, _source="mock") for p in _load_mock_dataset().values()]


def reset_cache() -> None:
    """Drop cached datasets — useful in tests after editing JSON files."""
    _load_mock_dataset.cache_clear()
    load_geo_risk.cache_clear()
