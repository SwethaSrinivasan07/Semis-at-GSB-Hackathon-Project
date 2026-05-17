import io
import pandas as pd

MPN_COLS  = ["MPN", "mpn", "Part Number", "PartNumber", "Part No", "Part_Number"]
MFR_COLS  = ["Manufacturer", "manufacturer", "Mfr", "MFR"]
QTY_COLS  = ["Qty", "qty", "Quantity", "quantity", "QTY"]
DESC_COLS = ["Description", "description", "Desc"]
REF_COLS  = ["Reference Designators", "Ref Des", "RefDes", "reference_designators"]


def _find(df, options):
    for o in options:
        if o in df.columns:
            return o
    return None


def parse_bom_simple(file_bytes: bytes, filename: str) -> list[dict]:
    """Parse BOM with pandas only — no Claude required."""
    df = pd.read_csv(io.BytesIO(file_bytes)) if filename.lower().endswith(".csv") else pd.read_excel(io.BytesIO(file_bytes))

    mpn_col  = _find(df, MPN_COLS)
    mfr_col  = _find(df, MFR_COLS)
    qty_col  = _find(df, QTY_COLS)
    desc_col = _find(df, DESC_COLS)
    ref_col  = _find(df, REF_COLS)

    parts = []
    for _, row in df.iterrows():
        mpn = str(row[mpn_col]).strip() if mpn_col else ""
        if not mpn or mpn.lower() == "nan":
            continue
        parts.append({
            "mpn": mpn,
            "manufacturer": str(row[mfr_col]).strip() if mfr_col else "",
            "quantity": int(row[qty_col]) if qty_col and pd.notna(row.get(qty_col)) else 1,
            "description": str(row[desc_col]).strip() if desc_col else "",
            "reference_designators": str(row[ref_col]).strip() if ref_col else "",
        })
    return parts


MOCK_SUBSTITUTES = {
    "GD25Q64CSIG": [
        {
            "mpn": "W25Q64JVSSIQ",
            "manufacturer": "Winbond",
            "compatibility_grade": "Drop-in",
            "key_differences": "Same 64Mbit SPI Flash, SOP-8 footprint, pin-compatible. Winbond is Taiwan-based, lower geo risk.",
            "why_better": "Eliminates China-sourced fab risk. Winbond W25Q64 is widely stocked at Digi-Key and Mouser with <4 week lead time.",
            "estimated_availability": "50,000+ units, 2–4 week lead time",
        },
        {
            "mpn": "MX25L6433FM2I-08G",
            "manufacturer": "Macronix",
            "compatibility_grade": "Drop-in",
            "key_differences": "64Mbit SPI NOR Flash, identical pinout and voltage range (2.7–3.6V). Taiwan-manufactured.",
            "why_better": "Macronix has diversified fab locations and strong distributor relationships. Available same week from Arrow.",
            "estimated_availability": "20,000+ units, 1–3 week lead time",
        },
        {
            "mpn": "IS25LP064A-JBLE",
            "manufacturer": "ISSI",
            "compatibility_grade": "Minor rework",
            "key_differences": "64Mbit SPI Flash, functionally identical but max clock speed is 133MHz vs 120MHz — minor firmware config change needed.",
            "why_better": "US-listed company with diversified Asian fab network. Good long-term supply stability.",
            "estimated_availability": "8,000+ units, 3–5 week lead time",
        },
    ],
    "XC7A35T-1CPG236C": [
        {
            "mpn": "XC7A35T-1FTG256C",
            "manufacturer": "Xilinx / AMD",
            "compatibility_grade": "Minor rework",
            "key_differences": "Same Artix-7 35T die, FTG256 package (256-ball vs 236-ball). PCB footprint change required but identical logic resources.",
            "why_better": "FTG256 package has significantly better distributor stock. Avoids NRND status risk on the CPG236 package variant.",
            "estimated_availability": "300+ units, 8–12 week lead time",
        },
        {
            "mpn": "10M04SAE144C8G",
            "manufacturer": "Intel / Altera",
            "compatibility_grade": "Redesign required",
            "key_differences": "MAX 10 FPGA family, different toolchain (Quartus vs Vivado), different I/O structure. Logic capacity is comparable.",
            "why_better": "Intel-sourced with US domestic fab options. Strong CHIPS Act investment. Long-term supply certainty.",
            "estimated_availability": "2,000+ units, 4–6 week lead time",
        },
        {
            "mpn": "LFE5U-25F-6BG256C",
            "manufacturer": "Lattice Semiconductor",
            "compatibility_grade": "Redesign required",
            "key_differences": "ECP5 family, different architecture and toolchain (Lattice Diamond). Low power advantage. BGA-256 package.",
            "why_better": "Lattice has avoided China-related export control concerns. US-headquartered with diversified supply chain.",
            "estimated_availability": "1,500+ units, 6–10 week lead time",
        },
    ],
    "IS42S16400J-7TL": [
        {
            "mpn": "AS4C16M16SA-7TCN",
            "manufacturer": "Alliance Memory",
            "compatibility_grade": "Drop-in",
            "key_differences": "64Mb SDRAM, identical 54-pin TSOP-II footprint and 143MHz operation. Pin and software compatible.",
            "why_better": "Alliance Memory maintains US-based engineering with diversified Asian manufacturing. Currently in stock.",
            "estimated_availability": "5,000+ units, 2–4 week lead time",
        },
        {
            "mpn": "MT48LC16M16A2P-6A:G",
            "manufacturer": "Micron Technology",
            "compatibility_grade": "Drop-in",
            "key_differences": "Industry-standard 64Mb SDRAM, drop-in compatible. Micron is US-manufactured with CHIPS Act investment.",
            "why_better": "Micron is a US domestic manufacturer — eliminates Taiwan concentration risk entirely. Highest supply stability.",
            "estimated_availability": "10,000+ units, 2–3 week lead time",
        },
    ],
    "MAX31855KASA+": [
        {
            "mpn": "MAX31856MUA+",
            "manufacturer": "Analog Devices (Maxim)",
            "compatibility_grade": "Minor rework",
            "key_differences": "Supports multiple thermocouple types (K, J, N, R, S, T, E, B). SPI-compatible but register map differs — firmware update needed.",
            "why_better": "Active product, not EOL. Direct Maxim replacement with better multi-type support and improved noise immunity.",
            "estimated_availability": "3,000+ units, 4–6 week lead time",
        },
        {
            "mpn": "MCP9600-E/MX",
            "manufacturer": "Microchip Technology",
            "compatibility_grade": "Minor rework",
            "key_differences": "I2C interface instead of SPI. Integrated cold-junction compensation. Requires firmware I2C driver update.",
            "why_better": "Active Microchip product with strong supply chain. US-headquartered with diversified fab network.",
            "estimated_availability": "8,000+ units, 2–4 week lead time",
        },
        {
            "mpn": "TMP116NAIDRLR",
            "manufacturer": "Texas Instruments",
            "compatibility_grade": "Redesign required",
            "key_differences": "Precision temperature sensor (not thermocouple interface). Requires separate cold-junction + analog front-end. I2C output.",
            "why_better": "TI has the deepest supply chain and largest distributor network globally. If redesign is feasible, this is the most resilient long-term choice.",
            "estimated_availability": "25,000+ units, 1–2 week lead time",
        },
    ],

    # ── Photonics BOM substitutes ─────────────────────────────────────────────

    "OP-27635": [
        {
            "mpn": "EFF-PIC-400-IQ",
            "manufacturer": "EFFECT Photonics",
            "compatibility_grade": "Drop-in",
            "key_differences": "InP IQ modulator, same C-band operation, comparable insertion loss. Netherlands-based fab — significantly lower geopolitical risk than US-sourced Coherent InP.",
            "why_better": "EFFECT Photonics is the leading independent InP PIC foundry with 8–12 week lead times vs Coherent's 60-week backlog. Eliminates single-source dependency entirely.",
            "estimated_availability": "Contact direct — 8–12 week lead time, qualification required",
        },
        {
            "mpn": "LMX-MOD-400G",
            "manufacturer": "Lumentum",
            "compatibility_grade": "Minor rework",
            "key_differences": "Lumentum InP modulator with slightly different drive voltage requirements (+/- 2V vs +/- 1.5V). Firmware and driver IC adjustment needed.",
            "why_better": "Lumentum maintains separate InP fab from Coherent — true supply diversification. Currently 30-week lead time vs 60 weeks. Already qualified at Nokia and Ciena.",
            "estimated_availability": "25 units in stock, 30–35 week replenishment",
        },
        {
            "mpn": "INTEL-SiPho-400",
            "manufacturer": "Intel",
            "compatibility_grade": "Redesign required",
            "key_differences": "Silicon Photonics platform — different material system (Si vs InP), different performance envelope. Requires full optical subassembly redesign but eliminates InP supply risk permanently.",
            "why_better": "Intel SiPho fab in Oregon — fully domestic, CHIPS Act protected, unlimited capacity scaling. Best long-term supply chain resilience if redesign timeline allows.",
            "estimated_availability": "Engineering samples available, volume: 16–20 week lead time",
        },
    ],

    "CFP2-DCO-400G": [
        {
            "mpn": "CFP2-400ZR-ACO",
            "manufacturer": "Acacia (Cisco)",
            "compatibility_grade": "Drop-in",
            "key_differences": "OIF-400ZR compliant CFP2 DCO, same form factor and electrical interface. Acacia uses Silicon Photonics vs Coherent's InP — different internal architecture but same MSA compliance.",
            "why_better": "Acacia/Cisco has committed significant capacity to non-hyperscaler OEMs. 26-week lead time vs 52 weeks. Already interoperable in Nokia lab testing.",
            "estimated_availability": "14 units in stock, 26-week replenishment lead time",
        },
        {
            "mpn": "CFP2-400ZR-INF",
            "manufacturer": "Infinera",
            "compatibility_grade": "Drop-in",
            "key_differences": "Infinera ICE7 coherent engine in CFP2 form factor, OIF-400ZR compliant. Infinera uses proprietary InP PIC but different supply chain from Coherent.",
            "why_better": "Post Nokia/Infinera merger, internal sourcing from Infinera avoids external procurement entirely — zero distributor cost. 20-week internal lead time.",
            "estimated_availability": "Internal sourcing post-merger — contact Infinera supply chain team",
        },
    ],

    "QSFP-DD-400G-ZR": [
        {
            "mpn": "QSFP-DD-400ZR-LMT",
            "manufacturer": "Lumentum",
            "compatibility_grade": "Drop-in",
            "key_differences": "OIF-400ZR compliant QSFP-DD, same electrical and optical interface. MSA standard ensures interoperability. Lumentum uses separate InP fab from Coherent.",
            "why_better": "Lumentum is already on AVL at most Tier-1 OEMs. 22-week lead time vs 38 weeks. Pricing 8% lower than Coherent at equivalent volumes.",
            "estimated_availability": "32 units in stock, 22-week replenishment",
        },
        {
            "mpn": "QSFP-DD-400ZR-ACO",
            "manufacturer": "Acacia (Cisco)",
            "compatibility_grade": "Drop-in",
            "key_differences": "Silicon Photonics based 400ZR QSFP-DD. OIF standard compliant — guaranteed interoperability. Lower power than InP-based alternatives (<9W vs <12W).",
            "why_better": "Best power efficiency in class. Acacia has confirmed non-hyperscaler allocation through 2026. 18-week lead time. Cisco backing provides supply chain stability.",
            "estimated_availability": "28 units in stock, 18-week replenishment",
        },
    ],

    "BCM88690": [
        {
            "mpn": "BCM88800",
            "manufacturer": "Broadcom",
            "compatibility_grade": "Minor rework",
            "key_differences": "Jericho3 successor — 25.6Tbps vs 12.8Tbps, same Broadcom SDK. Firmware and board power delivery update required. 5nm vs 7nm — better power efficiency.",
            "why_better": "Jericho3 has better availability than Jericho2c+ right now due to newer production ramp. Avoids EOL risk on Jericho2c+ in 18–24 months. Future-proofs the design.",
            "estimated_availability": "120 units in stock, 20-week replenishment",
        },
        {
            "mpn": "MV-Prestera-DX",
            "manufacturer": "Marvell",
            "compatibility_grade": "Redesign required",
            "key_differences": "Marvell Prestera switching ASIC — different SDK (Marvell CPSS vs Broadcom SDK). Requires full software stack port. Comparable switching capacity.",
            "why_better": "Marvell has stronger non-hyperscaler allocation commitments and lower pricing at volume. Eliminates Broadcom single-vendor ASIC dependency.",
            "estimated_availability": "280 units in stock, 16-week replenishment",
        },
    ],

    "ACO-DSP-400": [
        {
            "mpn": "GCX-DSP-400G",
            "manufacturer": "GlobeComm / Credo",
            "compatibility_grade": "Minor rework",
            "key_differences": "Credo Hawk DSP ASIC, comparable coherent performance, different API and control plane interface. 4-week firmware integration effort estimated.",
            "why_better": "Credo maintains dedicated OEM allocation separate from hyperscaler commitments. 18-week lead time vs 44 weeks. 15% cost reduction at volume.",
            "estimated_availability": "8 units in stock, 18-week lead time",
        },
    ],

    "FDMB5631": [
        {
            "mpn": "EAM-C-40G-LMT",
            "manufacturer": "Lumentum",
            "compatibility_grade": "Minor rework",
            "key_differences": "Lumentum InP EAM, 35GHz bandwidth vs 40GHz. Slightly lower bandwidth may require link budget adjustment. Same butterfly package and pin configuration.",
            "why_better": "Active product (Coherent FDMB5631 is NRND). Lumentum EAM has 24-week lead time vs 56 weeks and 3x the available stock.",
            "estimated_availability": "45 units in stock, 24-week replenishment",
        },
        {
            "mpn": "MZMO-LN-40",
            "manufacturer": "iXblue Photonics",
            "compatibility_grade": "Minor rework",
            "key_differences": "LiNbO3 Mach-Zehnder modulator vs InP EAM. Higher drive voltage (5V vs 2V), larger footprint — board layout change required. Proven technology with long lifecycle.",
            "why_better": "LiNbO3 modulators have no InP supply risk. iXblue (France-based) offers geopolitical diversification. Active product with 15+ year lifecycle guarantee.",
            "estimated_availability": "200+ units in stock, 6-week lead time",
        },
    ],
}


def get_mock_substitutes(mpn: str) -> list[dict]:
    return MOCK_SUBSTITUTES.get(mpn, [])
