"""
Distributor API client stubs.

Each class wraps a real distributor's HTTP API behind the same surface
(`search_part`, `get_pricing`). The HTTP calls are stubbed for the hackathon
demo — they return None today so distributor_api falls through to the mock
dataset — but the request shapes, auth patterns, and return contract are
real, so swapping in live keys is a one-line change per provider.

Add live credentials in .env (see .env.example).
"""

from __future__ import annotations

import logging
from typing import Any

import requests

log = logging.getLogger(__name__)

DEFAULT_TIMEOUT = 8  # seconds


class _BaseDistributorAPI:
    """Common shape so distributor_api.py can iterate clients uniformly."""

    source_name: str = "base"
    base_url: str = ""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()

    def search_part(self, mpn: str) -> dict[str, Any] | None:
        raise NotImplementedError

    def get_pricing(self, mpn: str, qty: int) -> dict[str, Any] | None:
        raise NotImplementedError

    def _to_contract(self, raw: dict[str, Any]) -> dict[str, Any]:
        """
        Subclasses translate vendor-specific response JSON into the shared
        part-record contract documented in distributor_api.py.
        """
        raise NotImplementedError


class DigiKeyAPI(_BaseDistributorAPI):
    """
    DigiKey Product Information v4.
    Auth: OAuth2 client credentials. The api_key here is treated as the
    bearer token issued from the OAuth handshake — production code should
    handle token refresh.
    """

    source_name = "digikey"
    base_url = "https://api.digikey.com/products/v4"

    def search_part(self, mpn: str) -> dict[str, Any] | None:
        # Stub: real implementation would POST to
        # /search/keyword with {"Keywords": mpn, "RecordCount": 1}
        # and translate the first ExactMatch result via _to_contract.
        log.debug("[stub] DigiKey.search_part(%s) — returning None (mock fallback)", mpn)
        return None

    def get_pricing(self, mpn: str, qty: int) -> dict[str, Any] | None:
        log.debug("[stub] DigiKey.get_pricing(%s, %s) — returning None", mpn, qty)
        return None

    def _to_contract(self, raw: dict[str, Any]) -> dict[str, Any]:
        return {
            "mpn": raw.get("ManufacturerProductNumber"),
            "manufacturer": (raw.get("Manufacturer") or {}).get("Name"),
            "category": (raw.get("Category") or {}).get("Name"),
            "description": raw.get("Description", {}).get("ProductDescription"),
            "price_usd": raw.get("UnitPrice"),
            "lead_time_weeks": raw.get("ManufacturerLeadWeeks"),
            "stock": raw.get("QuantityAvailable"),
            "lifecycle": raw.get("ProductStatus", {}).get("Status"),
            "fab_country": None,
            "package_country": None,
            "supplier_count": None,
            "alternates_available": None,
            "datasheet_url": raw.get("DatasheetUrl"),
            "rohs_compliant": raw.get("Classifications", {}).get("RohsStatus") == "Compliant",
            "notes": "",
            "last_updated": raw.get("DateLastBuyChance"),
        }


class MouserAPI(_BaseDistributorAPI):
    """
    Mouser Search API v2.
    Auth: api_key passed as `apiKey` query parameter.
    """

    source_name = "mouser"
    base_url = "https://api.mouser.com/api/v2"

    def search_part(self, mpn: str) -> dict[str, Any] | None:
        # Stub: real implementation would POST to
        # /search/partnumber?apiKey=... with body
        # {"SearchByPartRequest": {"mouserPartNumber": mpn, "partSearchOptions": "Exact"}}
        log.debug("[stub] Mouser.search_part(%s) — returning None (mock fallback)", mpn)
        return None

    def get_pricing(self, mpn: str, qty: int) -> dict[str, Any] | None:
        log.debug("[stub] Mouser.get_pricing(%s, %s) — returning None", mpn, qty)
        return None

    def _to_contract(self, raw: dict[str, Any]) -> dict[str, Any]:
        breaks = raw.get("PriceBreaks") or []
        unit = float(breaks[0]["Price"].replace("$", "")) if breaks else None
        return {
            "mpn": raw.get("ManufacturerPartNumber"),
            "manufacturer": raw.get("Manufacturer"),
            "category": raw.get("Category"),
            "description": raw.get("Description"),
            "price_usd": unit,
            "lead_time_weeks": raw.get("LeadTime"),
            "stock": int(raw.get("AvailabilityInStock") or 0),
            "lifecycle": raw.get("LifecycleStatus"),
            "fab_country": None,
            "package_country": None,
            "supplier_count": None,
            "alternates_available": None,
            "datasheet_url": raw.get("DataSheetUrl"),
            "rohs_compliant": raw.get("ROHSStatus") == "RoHS Compliant",
            "notes": "",
            "last_updated": None,
        }


class ArrowAPI(_BaseDistributorAPI):
    """
    Arrow ItemService API.
    Auth: api_key in `login` query parameter.
    Note: Arrow owns SiliconExpert, our primary competitor — using Arrow
    distributor data is fine for inventory lookups but we should treat their
    lifecycle/risk classifications with suspicion.
    """

    source_name = "arrow"
    base_url = "https://api.arrow.com/itemservice/v4"

    def search_part(self, mpn: str) -> dict[str, Any] | None:
        # Stub: GET /search/token?login=...&search_token=<mpn>
        log.debug("[stub] Arrow.search_part(%s) — returning None (mock fallback)", mpn)
        return None

    def get_pricing(self, mpn: str, qty: int) -> dict[str, Any] | None:
        log.debug("[stub] Arrow.get_pricing(%s, %s) — returning None", mpn, qty)
        return None

    def _to_contract(self, raw: dict[str, Any]) -> dict[str, Any]:
        return {
            "mpn": raw.get("partNumber"),
            "manufacturer": raw.get("manufacturer", {}).get("name"),
            "category": raw.get("category"),
            "description": raw.get("description"),
            "price_usd": raw.get("pricing", {}).get("unitPrice"),
            "lead_time_weeks": raw.get("leadTime", {}).get("weeks"),
            "stock": raw.get("inventory", {}).get("fohQuantity"),
            "lifecycle": raw.get("lifecycleStatus"),
            "fab_country": None,
            "package_country": None,
            "supplier_count": None,
            "alternates_available": None,
            "datasheet_url": raw.get("datasheetUrl"),
            "rohs_compliant": raw.get("compliance", {}).get("rohs") == "compliant",
            "notes": "",
            "last_updated": raw.get("lastUpdated"),
        }
