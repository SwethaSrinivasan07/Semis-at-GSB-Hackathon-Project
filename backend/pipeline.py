"""
pipeline.py — Full Analysis Pipeline
Catena | Jed's AI/LLM workstream

Single entry point for the frontend. Runs the complete analysis chain:
  1. Parse BOM  →  bom_parser
  2. Score risk  →  risk_engine
  3. Check AVL   →  avl_engine
  4. Suggest substitutes  →  substitution
  5. Generate narrative   →  risk_narrative

Frontend (Streamlit) calls run_full_analysis() and receives one dict
containing everything needed to render the dashboard.
"""

import os
from backend.bom_parser    import parse_bom, parse_bom_from_rows
from backend.risk_engine   import score_bom
from backend.avl_engine    import check_bom_avl_coverage, load_mock_avl, get_avl_summary
from backend.substitution  import suggest_bom_substitutes
from backend.risk_narrative import generate_narrative


def run_full_analysis(
    bom_input: str | list[dict],
    avl: dict | None = None,
    use_mock_avl: bool = True,
    run_substitution: bool = True,
) -> dict:
    """
    Run the complete Catena analysis pipeline on a BOM.

    Args:
        bom_input:        Either a raw BOM string (CSV text) or list of row dicts.
        avl:              Optional pre-loaded AVL dict. If None and use_mock_avl
                          is True, loads data/mock_avl.json automatically.
        use_mock_avl:     Load the demo mock AVL if no real AVL provided.
        run_substitution: Generate substitution suggestions (can skip to save
                          API calls during rapid iteration).

    Returns:
        {
            "parsed_parts":    list — raw parsed BOM
            "scored_parts":    list — parts with risk scores
            "avl_parts":       list — parts with AVL coverage
            "full_parts":      list — parts with risk + AVL + substitutes
            "bom_summary":     dict — RED/YELLOW/GREEN counts
            "avl_summary":     dict — AVL coverage stats
            "narrative":       str  — VP-level plain English briefing
            "oem_name":        str  — from AVL metadata
        }
    """
    # ── 1. Parse ──────────────────────────────────────────────────────────────
    if isinstance(bom_input, str):
        parsed = parse_bom(bom_input)
    else:
        parsed = parse_bom_from_rows(bom_input)

    # ── 2. Risk scoring ───────────────────────────────────────────────────────
    risk_result  = score_bom(parsed)
    scored_parts = risk_result["scored_parts"]
    bom_summary  = risk_result["summary"]

    # ── 3. AVL coverage ───────────────────────────────────────────────────────
    if avl is None and use_mock_avl:
        avl = load_mock_avl()

    if avl:
        avl_parts = check_bom_avl_coverage(scored_parts, avl)
    else:
        avl_parts = scored_parts  # no AVL provided, skip

    avl_summary = get_avl_summary(avl_parts) if avl else {}
    oem_name    = avl.get("oem_name", "Your OEM") if avl else "Your OEM"

    # ── 4. Substitution suggestions ───────────────────────────────────────────
    if run_substitution:
        full_parts = suggest_bom_substitutes(avl_parts, avl=avl)
    else:
        full_parts = [{**p, "substitutes": []} for p in avl_parts]

    # ── 5. Narrative ──────────────────────────────────────────────────────────
    narrative = generate_narrative(full_parts, bom_summary)

    return {
        "parsed_parts": parsed,
        "scored_parts": scored_parts,
        "avl_parts":    avl_parts,
        "full_parts":   full_parts,
        "bom_summary":  bom_summary,
        "avl_summary":  avl_summary,
        "narrative":    narrative,
        "oem_name":     oem_name,
    }
