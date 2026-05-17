import json
from pathlib import Path

DATA_DIR = Path(__file__).parent.parent / "data"

def _load_json(filename):
    with open(DATA_DIR / filename) as f:
        return json.load(f)

MOCK_DATA = _load_json("mock_distributor_data.json")
GEO_RISK = _load_json("geo_risk_map.json")


def get_part_data(mpn: str) -> dict:
    mpn_clean = mpn.strip()

    for key, data in MOCK_DATA.items():
        if key.upper() == mpn_clean.upper():
            part = data.copy()
            part["mpn"] = key
            fab = part.get("fab_location", "Unknown")
            geo = GEO_RISK.get(fab, GEO_RISK["Unknown"])
            part["geo_risk"] = geo["risk_level"]
            part["geo_risk_reason"] = geo["reason"]
            return part

    return {
        "mpn": mpn_clean,
        "description": "Part not found in database — data estimated",
        "manufacturer": "Unknown",
        "lifecycle_status": "Unknown",
        "unit_price": 0.0,
        "price_baseline": 0.0,
        "stock": 0,
        "provider": "Unknown",
        "lead_time_weeks": 0,
        "fab_location": "Unknown",
        "datasheet_url": "",
        "geo_risk": "MEDIUM",
        "geo_risk_reason": "Origin not identified",
    }
