"""
risk_engine.py — Photonics-Specific Supply Chain Risk Scorer
SupplyLine | Jed's AI/LLM workstream

Scores BOM components across 6 risk dimensions:
  Availability · Lead Time · Cost · Lifecycle · Geopolitical · Concentration

Photonics-specific market intelligence is baked into the system prompt so
Claude scores with real domain knowledge, not generic heuristics.
"""

import os
import json
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

RISK_DIMENSIONS = [
    "availability",
    "lead_time",
    "cost",
    "lifecycle",
    "geopolitical",
    "concentration",
]

# ── System prompt — loaded with current photonics market intelligence ──────────
_SYSTEM_PROMPT = """You are a senior supply chain risk analyst for photonics and optical
networking OEMs (Ciena, Nokia/Infinera, Arista, Cisco). You score component risk with
precision and current market awareness.

CURRENT MARKET INTELLIGENCE (as of mid-2025):

TRANSCEIVERS (400G / 800G):
- Industry-wide demand exceeds supply 2x (LightCounting Feb 2025)
- Coherent Corp: ~30-35% market share in 400G coherent; currently allocating ~60% of
  capacity to hyperscalers (Microsoft, Google, Meta, Amazon). OEM lead times 28-44 weeks.
- Lumentum: Strong alternative for coherent/DWDM; 14-20 week lead times.
- InnoLight / Eoptolink: Chinese vendors, 6-10 week lead times; eligible for non-carrier
  and enterprise programs but typically blocked by Tier-1 carrier flow-down clauses.
- Applied Optoelectronics (AOI): US-manufactured, 16-24 weeks, eligible for restricted progs.
- Sumitomo / Fujitsu: Japanese, 20-32 weeks, premium pricing.

InP PHOTONIC CHIPS (highest concentration risk in the industry):
- Only 3 InP PIC foundries exist globally: Coherent Corp (US), Fraunhofer HHI (Germany),
  one in China. Geopolitical RED for any US OEM.
- Lead times: 36-52 weeks. No short-term alternatives.

COHERENT DSPs:
- Cisco/Acacia and Marvell (Polaris/Orion) are the only volume suppliers.
- Since Cisco acquired Acacia in 2021, external DSP supply has tightened.
- Lead times: 26-40 weeks. Near-single-source risk for non-Cisco OEMs.

FPGAs:
- Intel Agilex / AMD Versal: both on TSMC advanced nodes; 24-40 week lead times due
  to AI-driven TSMC capacity allocation. AMD/Xilinx UltraScale generally shorter.

MEMORY:
- DDR5/HBM: Samsung, SK Hynix, Micron — generally available, 8-14 weeks.
- HBM specifically: SK Hynix dominant for H100/H200; some allocation constraints.

STANDARD POWER / ANALOG:
- Texas Instruments, ADI: mostly available, 8-18 weeks. Some PMICs tighter.

PASSIVES (MLCC, inductors):
- Murata, TDK, Yageo: 6-14 weeks, good availability. New AI server demand creating
  pockets of MLCC tightness for specific case sizes.

CONNECTORS:
- Molex, TE, Amphenol: generally 6-16 weeks. QSFP-DD cages can be 12-18 weeks.

GEOPOLITICAL CONTEXT:
- Taiwan risk: TSMC, many ASIC/SiPh fabs — elevated but manageable if alternatives exist.
- China-manufactured: US export control environment; OEM customer flow-down restrictions common.
- InP-specific: extreme concentration (see above).
- US/EU manufactured: lowest geopolitical risk."""


def score_part(part: dict) -> dict:
    """
    Score a single component across 6 risk dimensions using Claude.

    Args:
        part: dict from bom_parser (must contain at minimum: mpn, manufacturer,
              description, part_category)

    Returns:
        dict with keys:
            availability, lead_time, cost, lifecycle, geopolitical, concentration
              — each "RED" | "YELLOW" | "GREEN"
            composite_score      — "RED" if any dim RED, else "YELLOW" if any YELLOW, else "GREEN"
            risk_summary         — one-sentence description of primary risk
            lead_time_weeks_estimate — integer
            recommended_action   — "Monitor" | "Qualify alternate now" |
                                   "Place long-lead PO immediately" | "Escalate to VP level"
    """
    prompt = f"""Score this component for supply chain risk. Return ONLY valid JSON — no commentary.

COMPONENT:
{json.dumps(part, indent=2)}

SCORING RUBRIC:

availability — Stock accessible today across distributors + direct channels
  GREEN:  Readily available; multiple stocking distributors; no allocation
  YELLOW: Limited stock; on allocation; order lead time required
  RED:    On hard allocation; manufacturer prioritizing other customers; zero distributor stock

lead_time — Production lead time from manufacturer today
  GREEN:  < 14 weeks
  YELLOW: 14–28 weeks
  RED:    > 28 weeks

cost — Price stability and volatility risk
  GREEN:  Stable commodity pricing; no spot premium
  YELLOW: Moderate volatility; pricing pressure; 10-20% above historical
  RED:    Severe volatility; spot market 2x+ premium; or 10x+ price spikes observed

lifecycle — Product maturity and obsolescence risk
  GREEN:  Active production; recently qualified; multi-year roadmap confirmed
  YELLOW: Mature product; aging; no EOL announced but approaching end of life
  RED:    NRND (Not Recommended for New Designs); EOL announced; or last-time-buy situation

geopolitical — Geographic concentration and export-control risk
  GREEN:  US / EU / Japan manufactured; multiple geographic options
  YELLOW: Primarily Taiwan-sourced; single-region risk; moderate exposure
  RED:    InP PIC (only 3 fabs globally); China-manufactured with US flow-down risk;
          or Taiwan-only with zero geographic alternative

concentration — Number of qualified global suppliers for this specific component type
  GREEN:  4+ vendors globally can supply a qualified equivalent
  YELLOW: 2–3 vendors globally
  RED:    Single source; or only 1–2 vendors globally (e.g., InP PICs, coherent DSPs,
          custom ASICs with no equivalent)

SPECIAL PHOTONICS RULES (override general rubric):
- part_category = "photonic_ic": geopolitical → RED (always), concentration → RED (always)
- part_category = "coherent_dsp": concentration → RED (Cisco/Acacia + Marvell only)
- manufacturer = "Coherent Corp" AND part_category = "transceiver":
    availability → RED (60% capacity to hyperscalers), lead_time → RED (28-44 wks)
- part_category = "asic" with single named vendor: concentration → RED
- part_category = "fpga": lead_time → YELLOW minimum (24-40 wk TSMC crunch)

Return this exact JSON structure:
{{
  "availability": "RED|YELLOW|GREEN",
  "lead_time": "RED|YELLOW|GREEN",
  "cost": "RED|YELLOW|GREEN",
  "lifecycle": "RED|YELLOW|GREEN",
  "geopolitical": "RED|YELLOW|GREEN",
  "concentration": "RED|YELLOW|GREEN",
  "composite_score": "RED|YELLOW|GREEN",
  "risk_summary": "one sentence on primary risk",
  "lead_time_weeks_estimate": integer,
  "recommended_action": "Monitor|Qualify alternate now|Place long-lead PO immediately|Escalate to VP level"
}}"""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def score_bom(parts: list[dict]) -> dict:
    """
    Score all parts in a parsed BOM.

    Args:
        parts: list of dicts from bom_parser.parse_bom()

    Returns:
        dict with:
            scored_parts — list of parts, each with a "risk" sub-dict
            summary      — BOM-level aggregated stats
    """
    scored_parts = []
    for part in parts:
        risk = score_part(part)
        scored_parts.append({**part, "risk": risk})

    red   = [p for p in scored_parts if p["risk"]["composite_score"] == "RED"]
    yellow = [p for p in scored_parts if p["risk"]["composite_score"] == "YELLOW"]
    green  = [p for p in scored_parts if p["risk"]["composite_score"] == "GREEN"]

    return {
        "scored_parts": scored_parts,
        "summary": {
            "total_parts": len(scored_parts),
            "red_count": len(red),
            "yellow_count": len(yellow),
            "green_count": len(green),
            "critical_parts": [p["mpn"] for p in red],
            "overall_bom_risk": (
                "RED" if red else ("YELLOW" if yellow else "GREEN")
            ),
        },
    }
