"""
test_pipeline.py — Quick smoke test for the AI/LLM layer.

Run from repo root:
    ANTHROPIC_API_KEY=sk-... python test_pipeline.py

Tests each backend module individually, then the full pipeline.
Prints results to stdout — no test framework needed for hackathon.
"""

import os
import json
import sys

# ── Ensure ANTHROPIC_API_KEY is set ──────────────────────────────────────────
if not os.getenv("ANTHROPIC_API_KEY"):
    print("ERROR: ANTHROPIC_API_KEY not set. Export it and re-run.")
    sys.exit(1)


SAMPLE_BOM_TEXT = """Part Number,Description,Manufacturer,Quantity,Reference Designators
QSFP-DD-400G-ZR,400G ZR QSFP-DD Coherent Transceiver 120km,Coherent Corp,8,J1-J8
CFP2-DCO-100G,100G DWDM CFP2-DCO Coherent Module,Coherent Corp,4,J9-J12
INP-PIC-400G-TX,400G InP Photonic Integrated Circuit TX,II-VI,2,U1 U2
TPS546D24A,4.5V-17V 40A Step-Down Converter,Texas Instruments,12,U10-U21
AGFB014R24A2E2,Intel Agilex 5 FPGA,Intel,2,U3 U4
GRM188R61C106MAALD,100nF MLCC 0402 X5R,Murata,500,C1-C500
BCM56990,Tomahawk 4 400G Ethernet Switch ASIC,Broadcom,1,U5"""


def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def test_bom_parser():
    section("1. BOM PARSER")
    from backend.bom_parser import parse_bom
    parts = parse_bom(SAMPLE_BOM_TEXT)
    print(f"  Parsed {len(parts)} parts")
    for p in parts:
        print(f"  [{p['part_category']:15s}] {p['mpn']:30s} "
              f"single_source={p['is_single_source']}  "
              f"concentration={p['vendor_concentration']}")
    return parts


def test_risk_engine(parts):
    section("2. RISK ENGINE")
    from backend.risk_engine import score_bom
    result = score_bom(parts[:3])  # limit to 3 parts to save API calls
    summary = result["summary"]
    print(f"  RED={summary['red_count']}  YELLOW={summary['yellow_count']}  "
          f"GREEN={summary['green_count']}")
    for p in result["scored_parts"]:
        r = p["risk"]
        print(f"  [{r['composite_score']:6s}] {p['mpn']:30s} "
              f"lead={r['lead_time_weeks_estimate']}wk  "
              f"{r['risk_summary'][:60]}")
    return result


def test_avl_engine(parts):
    section("3. AVL ENGINE")
    from backend.avl_engine import load_mock_avl, check_bom_avl_coverage, get_avl_summary
    avl = load_mock_avl()
    print(f"  Loaded AVL for: {avl['oem_name']}")
    avl_parts = check_bom_avl_coverage(parts[:3], avl)
    for p in avl_parts:
        a = p["avl"]
        print(f"  on_avl={a['on_avl']}  gap={a['avl_gap']}  "
              f"vendors={a['avl_vendors']}  |  {p['mpn']}")
        print(f"    → {a['recommendation']}")
    return avl


def test_substitution(parts, avl):
    section("4. SUBSTITUTION ENGINE")
    from backend.substitution import suggest_substitutes
    # Test on the InP PIC — highest risk part
    inp_part = next((p for p in parts if p.get("part_category") == "photonic_ic"), parts[0])
    print(f"  Finding substitutes for: {inp_part['mpn']} ({inp_part['description']})")
    subs = suggest_substitutes(inp_part, avl=avl, max_suggestions=2)
    for s in subs:
        print(f"  [{s['compatibility_grade']:20s}] {s['manufacturer']:20s} "
              f"{s['estimated_availability']}wk  avl={s['is_avl_qualified']}  "
              f"qual={s['qualification_time']}wk")
        print(f"    why: {s['why_better']}")


def test_narrative(parts, avl):
    section("5. RISK NARRATIVE")
    from backend.risk_engine import score_bom
    from backend.avl_engine import check_bom_avl_coverage
    from backend.risk_narrative import generate_narrative
    scored = score_bom(parts)
    avl_parts = check_bom_avl_coverage(scored["scored_parts"], avl)
    narrative = generate_narrative(avl_parts, scored["summary"])
    print(f"\n  {narrative}\n")


def test_full_pipeline():
    section("6. FULL PIPELINE")
    from backend.pipeline import run_full_analysis
    result = run_full_analysis(
        SAMPLE_BOM_TEXT,
        use_mock_avl=True,
        run_substitution=True,
    )
    s = result["bom_summary"]
    print(f"  BOM: {s['total_parts']} parts | "
          f"RED={s['red_count']} YELLOW={s['yellow_count']} GREEN={s['green_count']}")
    print(f"\n  NARRATIVE:\n  {result['narrative']}\n")
    print("  Full pipeline: OK")


if __name__ == "__main__":
    parts = test_bom_parser()
    result = test_risk_engine(parts)
    avl    = test_avl_engine(parts)
    test_substitution(parts, avl)
    test_narrative(parts, avl)
    test_full_pipeline()
    print("\n✓ All tests passed\n")
