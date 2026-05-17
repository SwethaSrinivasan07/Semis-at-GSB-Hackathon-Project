"""
bom_parser.py — Photonics-Aware BOM Parser
SupplyLine | Jed's AI/LLM workstream

Parses raw BOM text or structured rows into normalized part records.
Photonics-specific: recognizes transceivers, PICs, coherent DSPs, merchant ASICs.
Handles messy BOMs: embedded part numbers, manufacturer name variants,
mixed description/MPN fields.
"""

import os
import json
import anthropic

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# ── System prompt — cached for reuse across many BOM rows ──────────────────────
_SYSTEM_PROMPT = """You are an expert hardware component engineer specializing in \
photonics and optical networking supply chains. You have deep knowledge of:

FORM FACTORS & STANDARDS
- Optical transceivers: QSFP-DD, QSFP28, QSFP+, CFP2, CFP2-ACO, CFP2-DCO,
  OSFP, SFP-DD, SFP28, SFP+ — all MSA-compliant pluggable optical modules
- Photonic Integrated Circuits (PICs): InP-based, Silicon Photonics (SiPh), GaAs
- Coherent DSPs: Acacia (now Cisco), Marvell Polaris / Orion, HiSilicon

VENDOR LANDSCAPE
Transceivers: Coherent Corp (formerly II-VI / Finisar), Lumentum (acquired Oclaro
  + NeoPhotonics), InnoLight (Zhongji), Eoptolink, Applied Optoelectronics (AOI),
  Sumitomo Electric, Fujitsu Optical, Accelink, Hisense Broadband, O-Net
InP PICs: Coherent Corp, Lumentum, EFFECT Photonics (Netherlands)
Silicon Photonics: Intel, Broadcom, Cisco/Luxtera, Marvell/Inphi
Merchant ASICs: Broadcom (Tomahawk, Trident, Jericho), Marvell (Prestera, Teralynx)
Coherent DSPs: Acacia/Cisco, Marvell (Polaris, Orion)
FPGAs: Intel (Agilex, Stratix), AMD/Xilinx (Versal, UltraScale+)
Power: Texas Instruments, Analog Devices (ADI / Maxim), Renesas, Monolithic Power
Memory: Samsung, SK Hynix, Micron
Timing: Microchip, TI, Silicon Labs
Passives: Murata, TDK, Yageo, Samsung Electro-Mechanics
Connectors: Molex, TE Connectivity, Amphenol

MANUFACTURER NAME NORMALIZATION
- "II-VI", "IIVI", "Finisar" → "Coherent Corp"
- "Viavi optical", "Oclaro", "NeoPhotonics" → "Lumentum"
- "Zhongji", "Zhongji Innolight" → "InnoLight"
- "Inphi" → "Marvell"
- "Acacia" → "Cisco/Acacia"
- "Altera" → "Intel"
- "Xilinx" → "AMD/Xilinx"
- "Maxim Integrated" → "Analog Devices"

You parse Bills of Materials and return precise, supply-chain-aware structured data."""


def parse_bom(raw_bom_text: str) -> list[dict]:
    """
    Parse raw BOM text (CSV content, pasted table, or description list) into
    a structured list of component records.

    Args:
        raw_bom_text: raw string — CSV rows, tab-separated, or freeform description

    Returns:
        List of dicts, each containing:
            mpn                  — manufacturer part number (str)
            manufacturer         — normalized vendor name (str)
            quantity             — integer unit count
            description          — clean part description (str)
            reference_designators — list of ref-des strings e.g. ["U1","U2"]
            part_category        — see taxonomy below (str)
            is_single_source     — true if ≤2 global suppliers (bool)
            vendor_concentration — "high" | "medium" | "low"
            form_factor          — MSA form factor for transceivers, else null
            speed_grade          — data rate for transceivers/ASICs, else null
            technology           — "InP" | "SiPh" | "GaAs" for PICs, else null
    """
    prompt = f"""Parse this Bill of Materials. Return ONLY a valid JSON array — no commentary.

PART CATEGORIES (use exactly these strings):
  "transceiver"       — pluggable optical modules (QSFP-DD, CFP2, OSFP, SFP28, etc.)
  "photonic_ic"       — photonic integrated circuits (InP PIC, SiPh chip)
  "coherent_dsp"      — coherent modem DSP chips (Acacia, Marvell Polaris/Orion)
  "asic"              — merchant switching/routing silicon (Broadcom, Marvell)
  "fpga"              — field-programmable gate arrays (Intel Agilex, AMD Versal)
  "power"             — PMICs, LDOs, voltage regulators, DC-DC converters
  "memory"            — DRAM, HBM, NAND, DDR modules
  "timing"            — clock generators, oscillators, timing ICs
  "passive"           — resistors, capacitors (MLCC), inductors, ferrites
  "connector"         — SFP/QSFP cages, board connectors, cable assemblies
  "optical_component" — discrete lasers, modulators, photodetectors, isolators
  "other"             — anything else

SINGLE-SOURCE RULES (is_single_source: true when):
  - Any InP PIC (only Coherent Corp, Lumentum, EFFECT Photonics globally)
  - Coherent DSPs (only Cisco/Acacia and Marvell)
  - Merchant ASICs listed as a specific named chip (e.g., Tomahawk 4) — captive
  - A transceiver listed with ONE specific named vendor and custom specs

VENDOR CONCENTRATION:
  "high"   — 1–2 global suppliers
  "medium" — 3–5 global suppliers
  "low"    — commodity, 6+ suppliers

For each part return this exact JSON structure:
{{
  "mpn": "string",
  "manufacturer": "normalized vendor name",
  "quantity": integer,
  "description": "clean description",
  "reference_designators": ["U1", "U2"],
  "part_category": "one of the categories above",
  "is_single_source": true/false,
  "vendor_concentration": "high|medium|low",
  "form_factor": "QSFP-DD or null",
  "speed_grade": "400G or null",
  "technology": "InP or SiPh or null"
}}

BOM TO PARSE:
{raw_bom_text}

Return ONLY the JSON array."""

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": prompt}],
    )

    raw = response.content[0].text.strip()
    # Strip markdown code fences if Claude wraps output
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def parse_bom_from_rows(rows: list[dict]) -> list[dict]:
    """
    Convenience wrapper: parse BOM from pre-loaded CSV rows (list of dicts).
    Converts to CSV text and calls parse_bom().

    Args:
        rows: list of dicts from csv.DictReader or pandas DataFrame.to_dict()

    Returns:
        Same structure as parse_bom()
    """
    if not rows:
        return []
    headers = list(rows[0].keys())
    lines = [",".join(headers)]
    for row in rows:
        lines.append(",".join(str(row.get(h, "")) for h in headers))
    return parse_bom("\n".join(lines))
