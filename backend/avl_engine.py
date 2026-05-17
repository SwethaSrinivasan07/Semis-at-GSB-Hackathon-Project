"""
avl_engine.py — AVL (Approved Vendor List) Awareness Engine
SupplyLine | Jed's AI/LLM workstream

This is SupplyLine's core differentiator vs. Octopart and SiliconExpert.
Neither knows your AVL. We do.

The AVL is the list of pre-qualified vendors an OEM can actually buy from.
Only AVL vendors can be used in production without a new qualification process.
Qualification for a transceiver takes 3-6 months. For an InP PIC: 6-18 months.
By the time you discover you need an alternate that's not on your AVL, you're
already months behind schedule.

This module:
  - Loads AVL data from JSON (per-MPN and per-category)
  - Checks AVL coverage for each BOM part
  - Flags AVL gaps (single vendor = critical risk)
  - Applies customer flow-down restrictions
  - Generates Claude-written procurement recommendations
"""

import os
import json
import anthropic
from pathlib import Path

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

_SYSTEM_PROMPT = """You are a component engineering expert for a photonics OEM. You
specialize in Approved Vendor List (AVL) management and know the real cost of supply
chain gaps:

QUALIFICATION TIME BENCHMARKS:
  Passive components (MLCC, resistors): 2–4 weeks
  Standard ICs, same pinout:           4–8 weeks
  Standard ICs, different pinout:      8–16 weeks
  Transceivers, same MSA standard:     3–6 months (interop, thermal, reliability, SNMP)
  Transceivers, different form factor: 4–8 months
  InP photonic chips:                  6–18 months (optical characterization + reliability)
  Technology change (InP → SiPh):      12–24 months (requires hardware redesign)

An AVL gap (only 1 vendor qualified) is not just a supply chain risk — it is a
program schedule risk. If that vendor goes on allocation, you cannot legally use a
substitute without completing qualification. Your recommendations must be actionable
and specific."""


def load_avl(avl_data: dict) -> dict:
    """
    Load and return a normalized AVL dict. Pass-through; validates structure.

    Expected avl_data format:
    {
        "oem_name": "...",
        "by_mpn": {
            "PART-MPN-123": ["Vendor A", "Vendor B"]
        },
        "by_category": {
            "transceiver": ["Coherent Corp", "Lumentum", "InnoLight"],
            "power": ["Texas Instruments", "Analog Devices"]
        },
        "customer_restrictions": {
            "Verizon": ["InnoLight", "Eoptolink"],
            "US Federal / DoD programs": ["InnoLight", "Eoptolink", "Accelink"]
        },
        "qualification_status": {
            "Coherent Corp": {"status": "Preferred", "since": "2018", "programs": ["all"]}
        }
    }
    """
    return avl_data


def check_avl_coverage(part: dict, avl: dict) -> dict:
    """
    Check AVL coverage for a single BOM part.

    Args:
        part: a parsed BOM part dict (from bom_parser)
        avl:  loaded AVL dict (from load_avl or load_mock_avl)

    Returns:
        dict with:
            on_avl           — bool: is the part's manufacturer on the AVL?
            avl_vendors      — list: all vendors qualified for this part/category
            avl_gap          — bool: only 0–1 vendor on AVL (critical risk flag)
            customer_conflicts — dict: {customer: [restricted_vendors_that_ARE_on_avl]}
            qualification_statuses — dict: {vendor: status_info} for each AVL vendor
            recommendation   — Claude-written one-sentence procurement guidance
    """
    mpn          = part.get("mpn", "")
    category     = part.get("part_category", "other")
    manufacturer = part.get("manufacturer", "")

    by_mpn       = avl.get("by_mpn", {})
    by_category  = avl.get("by_category", {})
    restrictions = avl.get("customer_restrictions", {})
    qual_status  = avl.get("qualification_status", {})

    # Resolve AVL vendors: MPN-specific takes precedence over category-level
    avl_vendors: list[str] = []
    if mpn in by_mpn:
        avl_vendors = list(by_mpn[mpn])
    elif category in by_category:
        avl_vendors = list(by_category[category])

    on_avl  = manufacturer in avl_vendors
    avl_gap = len(avl_vendors) <= 1

    # Customer conflicts: which customers restrict vendors that ARE on the AVL
    customer_conflicts: dict[str, list[str]] = {}
    for customer, blocked in restrictions.items():
        conflicted = [v for v in avl_vendors if v in blocked]
        if conflicted:
            customer_conflicts[customer] = conflicted

    # Pull qualification statuses for AVL vendors
    qualification_statuses = {
        v: qual_status.get(v, {"status": "Approved"})
        for v in avl_vendors
    }

    # Claude-generated recommendation
    prompt = f"""Write ONE actionable sentence for the supply chain team about this component's AVL status.

Component: {part.get('description', mpn)} ({mpn})
Manufacturer: {manufacturer}
Category: {category}
On AVL: {on_avl}
AVL Vendors: {avl_vendors}
AVL Gap (≤1 vendor): {avl_gap}
Customer Restrictions Conflicts: {customer_conflicts}
Qualification Statuses: {qualification_statuses}

Be specific: name vendors, call out the real risk (schedule slip, no approved alternate,
customer ineligibility). One sentence only."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=200,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    return {
        "on_avl": on_avl,
        "avl_vendors": avl_vendors,
        "avl_gap": avl_gap,
        "customer_conflicts": customer_conflicts,
        "qualification_statuses": qualification_statuses,
        "recommendation": response.content[0].text.strip(),
    }


def check_bom_avl_coverage(parts: list[dict], avl: dict) -> list[dict]:
    """
    Check AVL coverage for every part in a parsed BOM.

    Args:
        parts: list of parsed BOM part dicts
        avl:   loaded AVL dict

    Returns:
        Same list with an "avl" sub-dict added to each part.
    """
    return [{**part, "avl": check_avl_coverage(part, avl)} for part in parts]


def load_mock_avl() -> dict:
    """
    Load the mock Ciena-like OEM AVL from data/mock_avl.json.
    Used for the hackathon demo when no real AVL is uploaded.
    """
    avl_path = Path(__file__).parent.parent / "data" / "mock_avl.json"
    with open(avl_path, encoding="utf-8") as f:
        return json.load(f)


def get_avl_summary(avl_results: list[dict]) -> dict:
    """
    Summarize AVL coverage across the full BOM for dashboard display.

    Returns:
        dict with counts and lists of gap parts and conflict parts
    """
    total          = len(avl_results)
    on_avl         = sum(1 for p in avl_results if p.get("avl", {}).get("on_avl"))
    gaps           = [p for p in avl_results if p.get("avl", {}).get("avl_gap")]
    conflicts      = [p for p in avl_results if p.get("avl", {}).get("customer_conflicts")]
    not_on_avl     = [p for p in avl_results if not p.get("avl", {}).get("on_avl")]

    return {
        "total_parts": total,
        "on_avl_count": on_avl,
        "avl_gap_count": len(gaps),
        "customer_conflict_count": len(conflicts),
        "not_on_avl_count": len(not_on_avl),
        "avl_gap_parts": [p["mpn"] for p in gaps],
        "customer_conflict_parts": [p["mpn"] for p in conflicts],
    }
