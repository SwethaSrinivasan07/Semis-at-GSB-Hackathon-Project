LIFECYCLE_RISK = {
    "EOL": "RED",
    "Discontinued": "RED",
    "Obsolete": "RED",
    "NRND": "YELLOW",
    "Not Recommended for New Designs": "YELLOW",
    "Active": "GREEN",
    "Unknown": "YELLOW",
}

GEO_FLAG = {
    "HIGH": "RED",
    "MEDIUM": "YELLOW",
    "LOW": "GREEN",
    "UNKNOWN": "YELLOW",
}

STOCK_RED = 50
STOCK_YELLOW = 200
LEAD_RED = 20
LEAD_YELLOW = 8
PRICE_SPIKE_RED = 50   # percent above baseline
PRICE_SPIKE_YELLOW = 20


def score_part(part: dict) -> dict:
    flags = {}

    stock = part.get("stock", 0)
    if stock == 0:
        flags["availability"] = "RED"
    elif stock < STOCK_RED:
        flags["availability"] = "RED"
    elif stock < STOCK_YELLOW:
        flags["availability"] = "YELLOW"
    else:
        flags["availability"] = "GREEN"

    lead = part.get("lead_time_weeks", 0)
    if lead == 0:
        flags["lead_time"] = "YELLOW"
    elif lead > LEAD_RED:
        flags["lead_time"] = "RED"
    elif lead > LEAD_YELLOW:
        flags["lead_time"] = "YELLOW"
    else:
        flags["lead_time"] = "GREEN"

    price = part.get("unit_price", 0)
    baseline = part.get("price_baseline", price)
    if baseline and baseline > 0:
        pct = ((price - baseline) / baseline) * 100
        if pct > PRICE_SPIKE_RED:
            flags["cost"] = "RED"
        elif pct > PRICE_SPIKE_YELLOW:
            flags["cost"] = "YELLOW"
        else:
            flags["cost"] = "GREEN"
    else:
        flags["cost"] = "GREEN"

    lifecycle = part.get("lifecycle_status", "Unknown")
    flags["lifecycle"] = LIFECYCLE_RISK.get(lifecycle, "YELLOW")

    flags["geopolitical"] = GEO_FLAG.get(part.get("geo_risk", "UNKNOWN"), "YELLOW")

    values = list(flags.values())
    if "RED" in values:
        composite = "RED"
    elif "YELLOW" in values:
        composite = "YELLOW"
    else:
        composite = "GREEN"

    return {"flags": flags, "composite": composite}


def get_risk_summary(parts: list) -> dict:
    counts = {"RED": 0, "YELLOW": 0, "GREEN": 0}
    for p in parts:
        c = p.get("risk", {}).get("composite", "GREEN")
        counts[c] = counts.get(c, 0) + 1
    counts["total"] = len(parts)
    return counts
