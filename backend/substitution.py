"""
substitution.py — Photonics-Aware Component Substitution Engine
SupplyLine | Jed's AI/LLM workstream

Suggests qualified substitute components for at-risk BOM parts.
Photonics-specific: knows the full vendor landscape, MSA compatibility rules,
and the real cost of qualification (3-18 months for transceivers and PICs).

AVL-aware: prioritizes substitutes that are already on the OEM's AVL so
engineers don't trigger a new qualification cycle.
"""

import os
import json
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

_SYSTEM_PROMPT = """You are a component engineering expert for photonics and optical
networking OEMs. You suggest specific, actionable substitute components when primary
parts are constrained.

FULL VENDOR LANDSCAPE:

TRANSCEIVERS (400G/800G):
  Coherent Corp (US)        — Premium quality; dominant in coherent; 28-44 wk lead time;
                              hyperscaler-constrained right now
  Lumentum (US)             — Strong coherent/DWDM; 14-20 wk; good tier-1 carrier acceptance
  InnoLight / Zhongji (CN)  — Competitive pricing; 6-10 wk; typically blocked for carrier programs
  Eoptolink (CN)            — Similar to InnoLight; 4-8 wk
  Applied Optoelectronics (US) — US-manufactured; eligible for restricted programs; 16-24 wk
  Sumitomo Electric (JP)    — Telecom-grade reliability; 20-28 wk; premium pricing
  Fujitsu Optical (JP)      — DWDM and coherent focus; 22-32 wk
  Accelink (CN)             — Growing; 8-14 wk; carrier restrictions apply
  Hisense Broadband (CN)    — 400G/800G datacom; 6-12 wk; enterprise/hyperscale focus
  O-Net (CN)                — Multi-rate modules; 8-16 wk

InP PIC VENDORS (extremely limited — 3 foundries globally):
  Coherent Corp             — Primary volume source; 36-52 wk
  Lumentum                  — Post-Oclaro/NeoPhotonics; some InP capability; 40-52 wk
  EFFECT Photonics (NL)     — Emerging InP PIC vendor; smaller volumes; 6-12 mo qualification

SILICON PHOTONICS (technology alternative to InP for some applications):
  Intel (Intel Photonics)   — SiPh transceivers and components; requires redesign from InP
  Broadcom                  — SiPh for co-packaged optics
  Marvell/Inphi             — SiPh-based DSPs

COHERENT DSPs:
  Cisco/Acacia              — Best coherent performance; limited to Cisco ecosystem post-acq.
  Marvell (Polaris, Orion)  — Primary alternative; 26-36 wk

STANDARD IC CROSS-REFERENCES:
  Power:   Texas Instruments ↔ Analog Devices/Maxim ↔ Renesas ↔ Monolithic Power
           (generally pin-compatible within same function; verify specs)
  Memory:  Samsung ↔ SK Hynix ↔ Micron  (JEDEC standard; drop-in for same spec)
  FPGAs:   Intel Agilex ↔ AMD/Xilinx Versal  (NOT drop-in; requires firmware port)
  Timing:  Microchip ↔ Silicon Labs ↔ TI  (usually pin-compatible)
  Passives: Murata ↔ TDK ↔ Yageo ↔ Samsung EM  (drop-in within same spec)
  Connectors: Molex ↔ TE Connectivity ↔ Amphenol  (check mechanical fit)

QUALIFICATION TIME ESTIMATES:
  Passive components:              2–4 weeks
  Standard ICs (same pinout):      4–8 weeks
  Standard ICs (different pinout): 8–16 weeks
  Transceivers (same MSA):         3–6 months
  Transceivers (different MSA):    4–8 months
  InP PICs:                        6–18 months
  Technology change (InP→SiPh):    12–24 months

COMPATIBILITY GRADES:
  "Drop-in"          — Same form factor, pinout, protocol, MSA standard. No hardware change.
  "Minor rework"     — Same technology; different form factor (cage swap) OR minor firmware update.
  "Redesign required"— Different technology platform (InP→SiPh) OR major architecture change."""


def suggest_substitutes(
    part: dict,
    avl: dict | None = None,
    max_suggestions: int = 3,
) -> list[dict]:
    """
    Suggest substitute components for an at-risk BOM part.

    Args:
        part:            parsed BOM part dict (from bom_parser)
        avl:             optional loaded AVL dict (from avl_engine) for prioritization
        max_suggestions: max number of alternatives to return (default 3)

    Returns:
        List of substitute dicts, each containing:
            mpn                    — suggested MPN or descriptive identifier
            manufacturer           — vendor name
            compatibility_grade    — "Drop-in" | "Minor rework" | "Redesign required"
            key_differences        — list of 2-3 specific technical differences
            why_better             — supply chain advantage (lead time, geo, availability)
            estimated_availability — lead time estimate in weeks (int)
            is_avl_qualified       — bool: is this vendor already on the OEM's AVL?
            qualification_time     — estimated weeks to qualify (int)
            form_factor_compatible — bool: same MSA standard? (transceivers)
            design_change_required — description of required change, or null
    """
    # Resolve what vendors are on the AVL for this part's category
    avl_vendors: list[str] = []
    if avl:
        cat = part.get("part_category", "other")
        mpn = part.get("mpn", "")
        avl_vendors = (
            avl.get("by_mpn", {}).get(mpn, [])
            or avl.get("by_category", {}).get(cat, [])
        )

    prompt = f"""Suggest up to {max_suggestions} substitute components for this at-risk part.
Return ONLY a valid JSON array — no commentary.

AT-RISK COMPONENT:
{json.dumps(part, indent=2)}

OEM's AVL vendors for this category: {avl_vendors if avl_vendors else "Not provided — assume standard qualifications"}

SUBSTITUTION PRIORITY ORDER:
1. AVL-qualified vendors with shorter lead time (no new qualification needed)
2. Same MSA / same-pinout alternates from different geographic region
3. Technology alternatives only as last resort

For each substitute return this exact JSON structure:
{{
  "mpn": "specific MPN or descriptive identifier",
  "manufacturer": "vendor name",
  "compatibility_grade": "Drop-in|Minor rework|Redesign required",
  "key_differences": ["difference 1", "difference 2", "difference 3"],
  "why_better": "one sentence on the supply chain advantage",
  "estimated_availability": integer_weeks,
  "is_avl_qualified": true/false,
  "qualification_time": integer_weeks,
  "form_factor_compatible": true/false,
  "design_change_required": "description of change required" or null
}}

Return ONLY the JSON array."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def suggest_bom_substitutes(
    scored_parts: list[dict],
    avl: dict | None = None,
) -> list[dict]:
    """
    Generate substitution suggestions for all RED and YELLOW parts in a scored BOM.
    Skips GREEN parts to conserve API calls.

    Args:
        scored_parts: list from risk_engine.score_bom()["scored_parts"]
        avl:          optional AVL dict

    Returns:
        Same list with a "substitutes" key added to each part.
        GREEN parts get substitutes = [].
    """
    results = []
    for part in scored_parts:
        score = part.get("risk", {}).get("composite_score", "GREEN")
        if score in ("RED", "YELLOW"):
            subs = suggest_substitutes(part, avl=avl)
        else:
            subs = []
        results.append({**part, "substitutes": subs})
    return results
