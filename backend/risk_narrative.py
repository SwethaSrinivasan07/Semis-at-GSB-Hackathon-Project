"""
risk_narrative.py — VP-Level Supply Chain Risk Narrative Generator
SupplyLine | Jed's AI/LLM workstream

Generates a 3-5 sentence plain English risk briefing from a scored BOM.
Output is what a VP of Supply Chain or Hardware Engineering would want to
read in the 60 seconds before a program review.

Specific, actionable, names vendors and lead times. No boilerplate.
"""

import os
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

_SYSTEM_PROMPT = """You are a chief supply chain officer briefing an executive team at a
photonics OEM. You write concise, precise supply chain risk summaries.

Your audience: VP of Hardware Engineering or Chief Procurement Officer.
They have 60 seconds before a program review. They need to know:
  1. How bad is it overall?
  2. What is the single highest priority item and what should they do?
  3. What else is at risk?
  4. What is the immediate action?

Rules:
  - Name specific vendors (Coherent Corp, not "the supplier")
  - Name specific parts (InP PIC, not "optical component")
  - Cite lead times in weeks
  - Be direct about severity — do not soften RED risks
  - Do NOT use phrases like "it is important to note", "it should be mentioned",
    "supply chain landscape", or other corporate filler
  - 3–5 sentences maximum"""


def generate_narrative(parts_analyzed: list[dict], summary: dict) -> str:
    """
    Generate a plain English VP-level risk summary for a full BOM analysis.

    Args:
        parts_analyzed: scored (and optionally substitution/AVL-enriched) parts
                        from risk_engine, avl_engine, substitution pipeline
        summary:        BOM-level summary dict from risk_engine.score_bom()

    Returns:
        3–5 sentence narrative string suitable for a program review slide.
    """
    # Build a compact view of the most critical parts for the prompt
    at_risk = [
        p for p in parts_analyzed
        if p.get("risk", {}).get("composite_score") in ("RED", "YELLOW")
    ]

    # Sort: RED first, then YELLOW; within each group by lead time descending
    at_risk.sort(
        key=lambda p: (
            0 if p["risk"]["composite_score"] == "RED" else 1,
            -(p["risk"].get("lead_time_weeks_estimate") or 0),
        )
    )

    # Condense to what fits in a prompt without blowing context
    condensed = []
    for p in at_risk[:6]:
        avl_info = p.get("avl", {})
        subs     = p.get("substitutes", [])
        best_sub = subs[0]["manufacturer"] if subs else None

        condensed.append(
            f"- {p.get('description', p.get('mpn'))} ({p.get('mpn')}) | "
            f"Vendor: {p.get('manufacturer')} | "
            f"Risk: {p['risk']['composite_score']} | "
            f"Lead time: {p['risk'].get('lead_time_weeks_estimate', '?')} weeks | "
            f"{p['risk'].get('risk_summary', '')} | "
            f"AVL gap: {avl_info.get('avl_gap', 'unknown')} | "
            f"Best substitute: {best_sub or 'none identified'} | "
            f"Action: {p['risk'].get('recommended_action', 'Monitor')}"
        )

    prompt = f"""Write a 3-5 sentence supply chain risk briefing for a program review.

BOM OVERVIEW:
  Total parts analyzed:  {summary.get('total_parts', 0)}
  Critical (RED):        {summary.get('red_count', 0)}
  At-risk (YELLOW):      {summary.get('yellow_count', 0)}
  Healthy (GREEN):       {summary.get('green_count', 0)}
  Overall BOM risk:      {summary.get('overall_bom_risk', 'UNKNOWN')}

AT-RISK COMPONENTS (highest priority first):
{chr(10).join(condensed) if condensed else "  None — all parts GREEN"}

Write the briefing now. 3-5 sentences. Be direct and specific."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    return response.content[0].text.strip()
