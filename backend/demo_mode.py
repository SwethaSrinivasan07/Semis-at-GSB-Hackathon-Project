"""
End-to-end demo orchestration.

Glues distributor_api → risk_engine → substitution → report_generator into
a single runnable pipeline. The risk/substitution modules are imported
softly: if Jed's branch hasn't landed yet, lightweight fallback
implementations let the demo still work. Once the real modules are
present they take over automatically.

Run from repo root:
    python -m backend.demo_mode
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import distributor_api

REPO_ROOT = Path(__file__).resolve().parent.parent


SAMPLE_BOM: list[dict[str, Any]] = [
    {"ref_designator": "U1",  "mpn": "QSFP-DD-400G-ZR",         "qty": 32},
    {"ref_designator": "U2",  "mpn": "CFP2-DCO-400G",            "qty": 8},
    {"ref_designator": "U3",  "mpn": "OP-27635",                 "qty": 4},
    {"ref_designator": "U4",  "mpn": "BCM88690",                 "qty": 1},
    {"ref_designator": "U5",  "mpn": "ACO-DSP-400",              "qty": 2},
    {"ref_designator": "U6",  "mpn": "MV-ALASKA",                "qty": 2},
    {"ref_designator": "U7",  "mpn": "Si5345",                   "qty": 4},
    {"ref_designator": "U8",  "mpn": "LTC3892",                  "qty": 6},
    {"ref_designator": "U9",  "mpn": "STM32F407VGT6",            "qty": 1},
    {"ref_designator": "U10", "mpn": "XCKU040-2FFVA1156E",       "qty": 1},
    {"ref_designator": "U11", "mpn": "MT41K512M16HA-125",        "qty": 4},
    {"ref_designator": "U12", "mpn": "W25Q128JVSIQ",             "qty": 1},
    {"ref_designator": "U13", "mpn": "QSFP-DD-400G-DR4-INNOLIGHT", "qty": 16},
    {"ref_designator": "U14", "mpn": "TPS54620",                 "qty": 4},
]


# ---------- soft imports of teammate modules ----------------------------------

def _maybe_import(name: str):
    try:
        return __import__(f"backend.{name}", fromlist=[name])
    except Exception:
        return None


_risk_engine = _maybe_import("risk_engine")
_substitution = _maybe_import("substitution")
_risk_narrative = _maybe_import("risk_narrative")


# ---------- fallback risk scoring ---------------------------------------------

def _fallback_score(part: dict[str, Any], geo: dict[str, Any]) -> tuple[int, str, list[str]]:
    """
    Simple heuristic so the demo runs even without risk_engine. Score 0-100,
    higher = more risk. Mirrors the factors a real risk engine would weigh.
    """
    score = 0
    factors: list[str] = []

    if (part.get("supplier_count") or 99) <= 1:
        score += 35
        factors.append("Single-source globally")

    lt = part.get("lead_time_weeks") or 0
    if lt >= 40:
        score += 25
        factors.append(f"Lead time {lt} weeks")
    elif lt >= 20:
        score += 12
        factors.append(f"Lead time {lt} weeks")

    fab = part.get("fab_country")
    country_risk = (geo.get("countries", {}).get(fab) or {}).get("geo_risk_score", 0)
    if country_risk >= 8:
        score += 20
        factors.append(f"Geo risk: {fab} ({country_risk}/10)")
    elif country_risk >= 5:
        score += 10
        factors.append(f"Geo risk: {fab} ({country_risk}/10)")

    if (part.get("stock") or 0) < 50:
        score += 10
        factors.append(f"Low stock: {part.get('stock')}")

    lifecycle = (part.get("lifecycle") or "").upper()
    if lifecycle in ("NRND", "EOL", "OBSOLETE"):
        score += 15
        factors.append(f"Lifecycle: {part.get('lifecycle')}")

    score = min(score, 100)
    if score >= 60:
        level = "RED"
    elif score >= 30:
        level = "YELLOW"
    else:
        level = "GREEN"
    return score, level, factors


def _fallback_substitutes(part: dict[str, Any], all_parts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Suggest same-category alternates from a different manufacturer."""
    if not part:
        return []
    candidates = [
        p for p in all_parts
        if p.get("category") == part.get("category")
        and p.get("mpn") != part.get("mpn")
        and p.get("manufacturer") != part.get("manufacturer")
    ]
    candidates.sort(key=lambda p: ((p.get("supplier_count") or 99) * -1, p.get("lead_time_weeks") or 99))
    return candidates[:2]


# ---------- main pipeline -----------------------------------------------------

def analyze_bom(bom_lines: list[dict[str, Any]], bom_name: str = "Sample Nokia line card") -> dict[str, Any]:
    """
    Run the full analysis pipeline. Returns the analyzed-BOM dict that
    report_generator consumes.
    """
    geo = distributor_api.load_geo_risk()
    all_parts = distributor_api.get_all_parts()

    analyzed_lines: list[dict[str, Any]] = []
    for line in bom_lines:
        part = distributor_api.search_part(line["mpn"])
        if part is None:
            analyzed_lines.append({
                "ref_designator": line.get("ref_designator"),
                "qty": line.get("qty"),
                "mpn": line["mpn"],
                "part": None,
                "risk_score": 100,
                "risk_level": "RED",
                "risk_factors": ["Part not found in any distributor source"],
                "substitutes": [],
            })
            continue

        if _risk_engine and hasattr(_risk_engine, "score_part"):
            score, level, factors = _risk_engine.score_part(part, geo)
        else:
            score, level, factors = _fallback_score(part, geo)

        if _substitution and hasattr(_substitution, "find_substitutes"):
            subs = _substitution.find_substitutes(part, all_parts)
        else:
            subs = _fallback_substitutes(part, all_parts)

        analyzed_lines.append({
            "ref_designator": line.get("ref_designator"),
            "qty": line.get("qty"),
            "mpn": part["mpn"],
            "part": part,
            "risk_score": score,
            "risk_level": level,
            "risk_factors": factors,
            "substitutes": subs,
        })

    summary = _build_summary(analyzed_lines)
    narrative = ""
    if _risk_narrative and hasattr(_risk_narrative, "generate_narrative"):
        try:
            narrative = _risk_narrative.generate_narrative({"lines": analyzed_lines, "summary": summary})
        except Exception:
            narrative = ""
    if not narrative:
        narrative = _fallback_narrative(analyzed_lines, summary)

    return {
        "bom_name": bom_name,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "lines": analyzed_lines,
        "summary": summary,
        "narrative": narrative,
    }


def _build_summary(lines: list[dict[str, Any]]) -> dict[str, Any]:
    red = [l for l in lines if l["risk_level"] == "RED"]
    yellow = [l for l in lines if l["risk_level"] == "YELLOW"]
    green = [l for l in lines if l["risk_level"] == "GREEN"]
    top_risks = [
        f"{l['mpn']} ({(l['part'] or {}).get('manufacturer', '?')}) — {l['risk_factors'][0] if l['risk_factors'] else 'risk'}"
        for l in sorted(red, key=lambda x: -x["risk_score"])[:3]
    ]
    if not top_risks and yellow:
        top_risks = [
            f"{l['mpn']} ({(l['part'] or {}).get('manufacturer', '?')}) — {l['risk_factors'][0] if l['risk_factors'] else 'risk'}"
            for l in sorted(yellow, key=lambda x: -x["risk_score"])[:3]
        ]
    recommendation = _build_recommendation(red, yellow)
    return {
        "total_lines": len(lines),
        "red_count": len(red),
        "yellow_count": len(yellow),
        "green_count": len(green),
        "top_risks": top_risks,
        "recommendation": recommendation,
    }


def _build_recommendation(red: list[dict[str, Any]], yellow: list[dict[str, Any]]) -> str:
    if red:
        worst = max(red, key=lambda x: x["risk_score"])
        sub = worst["substitutes"][0] if worst["substitutes"] else None
        if sub:
            return (
                f"Qualify {sub['mpn']} ({sub['manufacturer']}) as a second source for "
                f"{worst['mpn']} before tape-out — it carries the highest single-line risk in this BOM."
            )
        return (
            f"{worst['mpn']} carries the highest risk and has no qualified alternates. "
            "Brief commodity management before design freeze."
        )
    if yellow:
        return "No critical risks, but several yellow items warrant a second-source review during DVT."
    return "No design-time supply chain risks detected. Proceed to layout."


def _fallback_narrative(lines: list[dict[str, Any]], summary: dict[str, Any]) -> str:
    n = summary["total_lines"]
    return (
        f"This BOM contains {n} parts. {summary['red_count']} are RED (high supply chain risk), "
        f"{summary['yellow_count']} YELLOW, {summary['green_count']} GREEN. "
        f"The dominant risk patterns are single-source photonic components and TSMC-fab dependencies on "
        f"the ASIC/DSP layer. Recommendation: {summary['recommendation']}"
    )


def run_demo(write_outputs: bool = True) -> dict[str, Any]:
    """
    Run the sample BOM through analysis. When write_outputs is true, also
    write JSON / PDF / Excel artifacts under repo/out/.
    """
    analysis = analyze_bom(SAMPLE_BOM)
    if write_outputs:
        out_dir = REPO_ROOT / "out"
        out_dir.mkdir(exist_ok=True)
        (out_dir / "analysis.json").write_text(
            json.dumps(analysis, indent=2, default=str), encoding="utf-8"
        )
        try:
            from . import report_generator

            report_generator.write_pdf(analysis, out_dir / "supplyline_report.pdf")
            report_generator.write_excel(analysis, out_dir / "supplyline_annotated_bom.xlsx")
        except Exception as exc:  # pragma: no cover - demo convenience
            print(f"[demo_mode] report generation skipped: {exc}")
    return analysis


if __name__ == "__main__":
    result = run_demo()
    s = result["summary"]
    print(f"BOM: {result['bom_name']}")
    print(f"  Lines: {s['total_lines']}  |  RED: {s['red_count']}  YELLOW: {s['yellow_count']}  GREEN: {s['green_count']}")
    print(f"  Top risks: {'; '.join(s['top_risks']) or 'none'}")
    print(f"  Recommendation: {s['recommendation']}")
