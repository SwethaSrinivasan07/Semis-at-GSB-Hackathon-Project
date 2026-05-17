"""
SupplyLine — Design-Time Supply Chain Intelligence for Photonics OEMs
"""

import io
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

# ─── Backend integration (graceful fallback) ─────────────────────────────────
try:
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from backend.analyzer import analyze_bom
    BACKEND_AVAILABLE = True
except ImportError:
    BACKEND_AVAILABLE = False

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SupplyLine",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─── CSS ─────────────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');

:root {
    --bg:            #F4F7FF;
    --surface:       #FFFFFF;
    --surface-2:     #F8FAFF;
    --border:        rgba(37,99,235,0.10);
    --border-strong: rgba(37,99,235,0.20);
    --accent:        #2563EB;
    --accent-hover:  #1D4ED8;
    --text-primary:  #0F172A;
    --text-secondary:#475569;
    --text-muted:    #94A3B8;
    --shadow-sm:     0 1px 3px rgba(15,23,42,0.04), 0 4px 16px rgba(15,23,42,0.06);
    --shadow-md:     0 4px 12px rgba(15,23,42,0.08), 0 16px 40px rgba(15,23,42,0.10);
    --shadow-accent: 0 0 0 3px rgba(37,99,235,0.12);
    --radius:        14px;
    --radius-sm:     8px;
    --transition:    all 0.22s cubic-bezier(0.4, 0, 0.2, 1);
}

html, body, [class*="css"] {
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}

/* ── App shell ── */
.stApp {
    background: var(--bg) !important;
}
.main .block-container {
    padding-top: 2.5rem;
    padding-bottom: 5rem;
    max-width: 1240px;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
    box-shadow: 2px 0 20px rgba(15,23,42,0.04) !important;
}
section[data-testid="stSidebar"] > div {
    background: var(--surface) !important;
    padding-top: 1.5rem;
}

/* ── Typography ── */
h1, h2, h3 {
    font-family: 'Playfair Display', Georgia, serif !important;
    font-weight: 700 !important;
    letter-spacing: -0.01em !important;
    color: var(--text-primary) !important;
}
p, li { color: var(--text-secondary); font-size: 0.875rem; }
label, .stTextInput label, .stNumberInput label, .stSelectbox label {
    color: var(--text-muted) !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.07em !important;
    text-transform: uppercase !important;
    font-weight: 600 !important;
}

/* ── Sidebar components ── */
.sidebar-logo {
    padding-bottom: 20px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 24px;
}
.sidebar-logo-title {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 1.2rem;
    font-weight: 700;
    color: var(--text-primary);
    letter-spacing: -0.01em;
}
.sidebar-logo-caption {
    font-size: 0.7rem;
    color: var(--text-muted);
    margin-top: 4px;
    font-weight: 500;
}
.sidebar-section {
    font-size: 0.65rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-muted);
    font-weight: 700;
    margin-top: 24px;
    margin-bottom: 12px;
    padding-bottom: 6px;
    border-bottom: 1px solid var(--border);
}

/* ── Metric cards ── */
.metric-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 14px;
    margin-bottom: 32px;
}
.metric-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px 24px;
    box-shadow: var(--shadow-sm);
    transition: var(--transition);
}
.metric-card:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-2px);
}
.metric-card-red   { border-top: 3px solid #EF4444; }
.metric-card-yellow{ border-top: 3px solid #F59E0B; }
.metric-card-green { border-top: 3px solid #10B981; }
.metric-label {
    font-size: 0.65rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-muted);
    font-weight: 700;
    margin-bottom: 10px;
}
.metric-value {
    font-family: 'Playfair Display', Georgia, serif;
    font-size: 2.4rem;
    font-weight: 700;
    color: var(--text-primary);
    line-height: 1;
    margin-bottom: 6px;
}
.metric-value-red    { color: #DC2626; }
.metric-value-yellow { color: #D97706; }
.metric-value-green  { color: #059669; }
.metric-sub {
    font-size: 0.72rem;
    color: var(--text-muted);
    font-weight: 500;
}

/* ── Risk pills ── */
.pill {
    display: inline-block;
    border-radius: 9999px;
    padding: 3px 11px;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    border: 1px solid;
    white-space: nowrap;
}
.pill-RED    { background: #FEF2F2; border-color: #FECACA; color: #B91C1C; }
.pill-YELLOW { background: #FFFBEB; border-color: #FDE68A; color: #92400E; }
.pill-GREEN  { background: #ECFDF5; border-color: #A7F3D0; color: #065F46; }

/* ── Risk dot ── */
.risk-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}
.dot-RED    { background: #EF4444; }
.dot-YELLOW { background: #F59E0B; }
.dot-GREEN  { background: #10B981; }

/* ── Risk breakdown strip ── */
.risk-strip {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    margin: 10px 0 20px 0;
}
.risk-dim {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 5px;
}
.risk-dim-label {
    font-size: 0.6rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--text-muted);
    font-weight: 600;
}

/* ── Detail section inside expander ── */
.detail-section-header {
    font-size: 0.63rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: var(--text-muted);
    font-weight: 700;
    margin-bottom: 10px;
    margin-top: 20px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border);
}
.detail-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0 40px;
}
.detail-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid var(--border);
}
.detail-key {
    font-size: 0.7rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: var(--text-muted);
    font-weight: 600;
}
.detail-val {
    font-size: 0.82rem;
    color: var(--text-secondary);
    text-align: right;
    font-weight: 500;
}

/* ── Substitute cards ── */
.sub-card {
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 14px 18px;
    margin-bottom: 10px;
    transition: var(--transition);
    box-shadow: var(--shadow-sm);
}
.sub-card:hover {
    box-shadow: var(--shadow-md);
    transform: translateY(-1px);
}
.sub-drop-in  { border-left: 4px solid #10B981; }
.sub-minor    { border-left: 4px solid #F59E0B; }
.sub-redesign { border-left: 4px solid #EF4444; }
.sub-header {
    display: flex;
    align-items: center;
    gap: 10px;
    margin-bottom: 8px;
}
.sub-mpn {
    font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
    font-weight: 700;
    font-size: 0.85rem;
    color: var(--text-primary);
}
.sub-mfr {
    font-size: 0.75rem;
    color: var(--text-muted);
    font-weight: 500;
}
.sub-grade-spacer { margin-left: auto; }
.sub-diff  { font-size: 0.78rem; color: var(--text-secondary); margin-top: 5px; }
.sub-why   { font-size: 0.78rem; color: var(--text-primary);   margin-top: 5px; font-weight: 500; }
.sub-avail { font-size: 0.73rem; color: var(--text-muted);     margin-top: 5px; }

/* ── Expander → premium white card ── */
[data-testid="stExpander"] {
    background: var(--surface) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    margin-bottom: 8px !important;
    overflow: hidden;
    box-shadow: var(--shadow-sm) !important;
    transition: var(--transition) !important;
}
[data-testid="stExpander"]:hover {
    box-shadow: var(--shadow-md) !important;
    border-color: var(--border-strong) !important;
    transform: translateY(-2px);
}
[data-testid="stExpander"] > details {
    background: var(--surface) !important;
}
[data-testid="stExpander"] summary {
    color: var(--text-primary) !important;
    background: var(--surface) !important;
    padding: 14px 20px !important;
    font-size: 0.875rem !important;
}
[data-testid="stExpander"] summary:hover {
    background: var(--surface-2) !important;
}
[data-testid="stExpander"] summary svg {
    fill: var(--text-muted) !important;
}
[data-testid="stExpander"] > details > div {
    background: var(--surface) !important;
    border-top: 1px solid var(--border) !important;
    padding: 20px !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: var(--surface);
    border-radius: var(--radius);
    padding: 4px;
}
[data-testid="stFileUploader"] > div {
    background: transparent !important;
}
[data-testid="stFileUploadDropzone"] {
    background: var(--surface) !important;
    border: 1.5px dashed var(--border-strong) !important;
    border-radius: var(--radius) !important;
    transition: var(--transition) !important;
}
[data-testid="stFileUploadDropzone"]:hover {
    border-color: var(--accent) !important;
    background: rgba(37,99,235,0.03) !important;
}
[data-testid="stFileUploadDropzone"] p,
[data-testid="stFileUploadDropzone"] span {
    color: var(--text-muted) !important;
}

/* ── Buttons ── */
.stButton > button {
    background: var(--surface) !important;
    border: 1px solid var(--border-strong) !important;
    color: var(--text-secondary) !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    box-shadow: var(--shadow-sm) !important;
    transition: var(--transition) !important;
}
.stButton > button:hover {
    background: var(--surface-2) !important;
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    transform: translateY(-1px);
    box-shadow: var(--shadow-md) !important;
}
.stButton > button:active {
    transform: translateY(0) scale(0.98) !important;
}
[data-testid="baseButton-primary"] {
    background: var(--accent) !important;
    border: none !important;
    color: #ffffff !important;
    font-weight: 700 !important;
    border-radius: var(--radius-sm) !important;
    box-shadow: 0 2px 8px rgba(37,99,235,0.30) !important;
}
[data-testid="baseButton-primary"]:hover {
    background: var(--accent-hover) !important;
    box-shadow: 0 4px 16px rgba(37,99,235,0.40) !important;
    transform: translateY(-1px) scale(1.01) !important;
}

/* ── Download buttons ── */
[data-testid="stDownloadButton"] button {
    background: var(--surface) !important;
    border: 1px solid var(--border-strong) !important;
    color: var(--text-secondary) !important;
    border-radius: var(--radius-sm) !important;
    font-size: 0.82rem !important;
    font-weight: 600 !important;
    box-shadow: var(--shadow-sm) !important;
    transition: var(--transition) !important;
}
[data-testid="stDownloadButton"] button:hover {
    border-color: var(--accent) !important;
    color: var(--accent) !important;
    transform: translateY(-1px) !important;
    box-shadow: var(--shadow-md) !important;
}

/* ── Inputs ── */
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"]   input {
    background: var(--surface) !important;
    border: 1px solid var(--border-strong) !important;
    color: var(--text-primary) !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'Plus Jakarta Sans', sans-serif !important;
}
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextInput"]   input:focus {
    border-color: var(--accent) !important;
    box-shadow: var(--shadow-accent) !important;
}
[data-testid="stNumberInput"] > div,
[data-testid="stTextInput"]   > div {
    background: var(--surface) !important;
    border-color: var(--border-strong) !important;
}

/* ── Toggles ── */
[data-testid="stToggle"] span[data-checked="true"] {
    background: var(--accent) !important;
}

/* ── Alerts ── */
[data-testid="stInfo"] {
    background: rgba(37,99,235,0.06) !important;
    border: 1px solid rgba(37,99,235,0.20) !important;
    color: #1E40AF !important;
    border-radius: var(--radius-sm) !important;
}
[data-testid="stWarning"] {
    background: #FFFBEB !important;
    border: 1px solid #FDE68A !important;
    border-radius: var(--radius-sm) !important;
}
[data-testid="stError"] {
    background: #FEF2F2 !important;
    border: 1px solid #FECACA !important;
    border-radius: var(--radius-sm) !important;
}

/* ── Dividers ── */
hr { border-color: var(--border) !important; margin: 24px 0 !important; }

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 100px 20px;
}
.empty-state-icon { font-size: 3rem; margin-bottom: 20px; opacity: 0.4; }
.empty-state-text {
    font-size: 0.95rem;
    color: var(--text-muted);
    font-weight: 500;
    line-height: 1.6;
}

/* ── Hero header gradient ── */
.app-hero {
    background: linear-gradient(135deg, rgba(37,99,235,0.06) 0%, rgba(99,102,241,0.04) 50%, transparent 100%);
    border-radius: 20px;
    padding: 32px 36px 28px;
    margin-bottom: 32px;
    border: 1px solid rgba(37,99,235,0.08);
}
.app-hero h1 {
    font-family: 'Playfair Display', Georgia, serif !important;
    font-size: 2.2rem !important;
    font-weight: 700 !important;
    color: var(--text-primary) !important;
    margin-bottom: 8px !important;
    line-height: 1.2 !important;
}
.app-hero p {
    color: var(--text-muted) !important;
    font-size: 0.9rem !important;
    margin: 0 !important;
    font-weight: 500 !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: var(--bg); }
::-webkit-scrollbar-thumb { background: var(--border-strong); border-radius: 4px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent); }

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)


# ─── Sample data ─────────────────────────────────────────────────────────────
SAMPLE_BOM_CSV = """\
Part Number,Manufacturer,Quantity,Reference Designators,Description
OP-27635,Coherent,4,"PIC1,PIC4",InP Photonic Integrated Circuit — coherent modulator
QSFP-DD-400G-DR4,Coherent,12,"Q1,Q2,Q12",400G QSFP-DD DR4 Transceiver
INPHI-K200Q2-1,Marvell (Inphi),8,"DSP1,DSP8",400G Coherent DSP ASIC
GN1103-DQFP,Semtech,24,"CDR1,CDR24",100G PAM4 CDR IC
LX2160ACPE24-RE,NXP Semiconductors,4,"IC1,IC4",16-core Network SoC
CXO7050Q8-106.25,Crystek,4,"XTAL1,XTAL4",106.25 MHz VCXO LVPECL
AFCT-5765ATZ,Broadcom,48,"U1,U48",10GBASE-SR SFP+ Transceiver
TAS5766MDCA,Texas Instruments,16,"U10,U26",Class-D Amplifier IC
VSC8514XKN,Microchip Technology,2,"PHY1,PHY2",Quad-port GbE PHY
"""

SAMPLE_RESULTS = [
    {
        "mpn": "OP-27635",
        "manufacturer": "Coherent Corp.",
        "quantity": 4,
        "reference_designators": ["PIC1", "PIC2", "PIC3", "PIC4"],
        "description": "InP Photonic Integrated Circuit — coherent modulator/demodulator for 400G ZR+ line cards",
        "distributor_data": {
            "description": "InP PIC coherent modulator, 400G ZR+ capable, dual-polarization IQ modulator",
            "manufacturer": "Coherent Corp.",
            "lifecycle_status": "Active",
            "unit_price": 8400.00,
            "stock": 8,
            "provider": "Direct (Coherent FAE only)",
            "lead_time_weeks": 60,
            "fab_location": "USA (Coherent Bloomfield CT InP fab)",
            "datasheet_url": "",
            "geo_risk": "HIGH",
        },
        "risk": {
            "composite": "RED",
            "flags": {
                "availability": "RED",
                "lead_time": "RED",
                "cost": "RED",
                "lifecycle": "GREEN",
                "geopolitical": "RED",
            },
        },
        "substitutes": [
            {
                "mpn": "EFF-InP-PIC-400G",
                "manufacturer": "EFFECT Photonics",
                "compatibility_grade": "drop-in",
                "key_differences": "Equivalent InP PIC, same modulator architecture, MSA footprint compatible",
                "why_better": "Alternate InP source — breaks single-supplier lock; 18-week qualification vs 60-week lead",
                "estimated_availability": "Engineering samples in 8 weeks; production 18 weeks",
            },
            {
                "mpn": "LMX-ICIX-400ZR",
                "manufacturer": "Lumentum",
                "compatibility_grade": "minor-rework",
                "key_differences": "Different bias voltage range; requires DSP firmware tuning for Lumentum PIC",
                "why_better": "US fab, active production ramp, second source for InP coherent PICs",
                "estimated_availability": "45 units available, 22-week lead for production volumes",
            },
            {
                "mpn": "SiPh-400G-MOD",
                "manufacturer": "Intel / Tower Semiconductor",
                "compatibility_grade": "redesign-required",
                "key_differences": "Silicon photonics — different loss profile and chirp characteristics; needs carrier board respin",
                "why_better": "Long-term resilience: SiPh fabs are 10x more numerous than InP; eliminates geo concentration risk",
                "estimated_availability": "Design kit available now; tape-out in 6 months",
            },
        ],
    },
    {
        "mpn": "QSFP-DD-400G-DR4",
        "manufacturer": "Coherent Corp.",
        "quantity": 12,
        "reference_designators": ["Q1", "Q2", "Q12"],
        "description": "400G QSFP-DD DR4 Single-Mode Optical Transceiver, 1310nm, 500m reach",
        "distributor_data": {
            "description": "400G QSFP-DD DR4 Transceiver, 1310nm SMF",
            "manufacturer": "Coherent Corp.",
            "lifecycle_status": "Active",
            "unit_price": 1250.00,
            "stock": 18,
            "provider": "Arrow Electronics",
            "lead_time_weeks": 26,
            "fab_location": "China",
            "datasheet_url": "",
            "geo_risk": "HIGH",
        },
        "risk": {
            "composite": "RED",
            "flags": {
                "availability": "RED",
                "lead_time": "RED",
                "cost": "YELLOW",
                "lifecycle": "GREEN",
                "geopolitical": "RED",
            },
        },
        "substitutes": [
            {
                "mpn": "FTQSFPDD4x100SM",
                "manufacturer": "Finisar (II-VI)",
                "compatibility_grade": "drop-in",
                "key_differences": "Same 400G DR4 spec, MSA compliant, identical footprint",
                "why_better": "US-allied fab option, 6-week lead vs 26 weeks, 120 units in stock",
                "estimated_availability": "120 units available, 6-week lead time",
            },
            {
                "mpn": "AFCT-9705Z",
                "manufacturer": "Broadcom",
                "compatibility_grade": "minor-rework",
                "key_differences": "Different TX power range, requires firmware config update",
                "why_better": "340 units in stock, US-allied fab, significantly lower geo risk",
                "estimated_availability": "340 units, ships in 2 weeks",
            },
        ],
    },
    {
        "mpn": "INPHI-K200Q2-1",
        "manufacturer": "Marvell Technology",
        "quantity": 8,
        "reference_designators": ["DSP1", "DSP2", "DSP8"],
        "description": "400G Coherent DSP ASIC, PAM4, 7nm FinFET, for CFP2-DCO applications",
        "distributor_data": {
            "description": "Colorz II 400G Coherent DSP IC",
            "manufacturer": "Marvell Technology",
            "lifecycle_status": "Active",
            "unit_price": 3200.00,
            "stock": 0,
            "provider": "Direct (Marvell FAE)",
            "lead_time_weeks": 52,
            "fab_location": "Taiwan (TSMC 7nm)",
            "datasheet_url": "",
            "geo_risk": "HIGH",
        },
        "risk": {
            "composite": "RED",
            "flags": {
                "availability": "RED",
                "lead_time": "RED",
                "cost": "RED",
                "lifecycle": "GREEN",
                "geopolitical": "RED",
            },
        },
        "substitutes": [
            {
                "mpn": "ACACIA-400ZR-DSP",
                "manufacturer": "Cisco (Acacia)",
                "compatibility_grade": "redesign-required",
                "key_differences": "Different pin-out and power domain layout, requires carrier board spin",
                "why_better": "US company with domestic supply visibility; NDA pricing available",
                "estimated_availability": "Eval samples in 8 weeks; production at 20 weeks",
            },
        ],
    },
    {
        "mpn": "GN1103-DQFP",
        "manufacturer": "Semtech",
        "quantity": 24,
        "reference_designators": ["CDR1", "CDR24"],
        "description": "100G PAM4 SiGe CDR (Clock-Data Recovery), single-channel, -40 to +85°C",
        "distributor_data": {
            "description": "100G PAM4 CDR for optical line card applications",
            "manufacturer": "Semtech",
            "lifecycle_status": "NRND",
            "unit_price": 88.00,
            "stock": 60,
            "provider": "Future Electronics",
            "lead_time_weeks": 32,
            "fab_location": "USA (GF Essex Jct)",
            "datasheet_url": "",
            "geo_risk": "LOW",
        },
        "risk": {
            "composite": "RED",
            "flags": {
                "availability": "RED",
                "lead_time": "RED",
                "cost": "YELLOW",
                "lifecycle": "RED",
                "geopolitical": "GREEN",
            },
        },
        "substitutes": [
            {
                "mpn": "DS250DF810SEQ",
                "manufacturer": "Texas Instruments",
                "compatibility_grade": "minor-rework",
                "key_differences": "Different CDR lock range; requires VCO tuning adjustment in firmware",
                "why_better": "Active lifecycle, 4,500 units in stock, US fab, drop-in footprint",
                "estimated_availability": "In stock — 3-week lead time",
            },
        ],
    },
    {
        "mpn": "LX2160ACPE24-RE",
        "manufacturer": "NXP Semiconductors",
        "quantity": 4,
        "reference_designators": ["IC1", "IC2", "IC3", "IC4"],
        "description": "16-core ARM Cortex-A72 Network Processing SoC, 25G Ethernet, TSMC 7nm",
        "distributor_data": {
            "description": "LayerScape LX2160A 16-core SoC with integrated 25G Ethernet",
            "manufacturer": "NXP Semiconductors",
            "lifecycle_status": "Active",
            "unit_price": 482.00,
            "stock": 45,
            "provider": "Digi-Key",
            "lead_time_weeks": 20,
            "fab_location": "Taiwan (TSMC 7nm)",
            "datasheet_url": "",
            "geo_risk": "MEDIUM",
        },
        "risk": {
            "composite": "YELLOW",
            "flags": {
                "availability": "YELLOW",
                "lead_time": "RED",
                "cost": "GREEN",
                "lifecycle": "GREEN",
                "geopolitical": "YELLOW",
            },
        },
        "substitutes": [
            {
                "mpn": "LS1088ARDB",
                "manufacturer": "NXP Semiconductors",
                "compatibility_grade": "redesign-required",
                "key_differences": "8-core vs 16-core; different SerDes config, requires BSP port",
                "why_better": "Better stock position, shorter lead, US-NXP domestic inventory",
                "estimated_availability": "200 units, 8-week lead time",
            },
        ],
    },
    {
        "mpn": "CXO7050Q8-106.25",
        "manufacturer": "Crystek Corp.",
        "quantity": 4,
        "reference_designators": ["XTAL1", "XTAL2", "XTAL3", "XTAL4"],
        "description": "106.25 MHz VCXO ±50ppm, LVPECL output, −40 to +85°C, 5×7mm SMD",
        "distributor_data": {
            "description": "Voltage-Controlled Crystal Oscillator 106.25MHz LVPECL",
            "manufacturer": "Crystek Corp.",
            "lifecycle_status": "Active",
            "unit_price": 38.40,
            "stock": 180,
            "provider": "Digi-Key",
            "lead_time_weeks": 10,
            "fab_location": "USA",
            "datasheet_url": "",
            "geo_risk": "LOW",
        },
        "risk": {
            "composite": "YELLOW",
            "flags": {
                "availability": "GREEN",
                "lead_time": "YELLOW",
                "cost": "RED",
                "lifecycle": "GREEN",
                "geopolitical": "GREEN",
            },
        },
        "substitutes": [
            {
                "mpn": "ABLNO-V-106.250MHz",
                "manufacturer": "Abracon",
                "compatibility_grade": "drop-in",
                "key_differences": "Equivalent LVPECL 106.25 MHz VCXO, same 5×7mm SMD footprint",
                "why_better": "30% lower price point, 500 units in stock with immediate availability",
                "estimated_availability": "500 units — ships immediately",
            },
        ],
    },
    {
        "mpn": "AFCT-5765ATZ",
        "manufacturer": "Broadcom",
        "quantity": 48,
        "reference_designators": ["U1", "U2", "U3", "U48"],
        "description": "10GBASE-SR SFP+ Optical Transceiver Module, 850nm, 300m reach, 0–70°C",
        "distributor_data": {
            "description": "10GBASE-SR SFP+ Transceiver, 850nm, 300m",
            "manufacturer": "Broadcom Inc.",
            "lifecycle_status": "Active",
            "unit_price": 45.50,
            "stock": 2400,
            "provider": "Avnet",
            "lead_time_weeks": 4,
            "fab_location": "Taiwan",
            "datasheet_url": "",
            "geo_risk": "LOW",
        },
        "risk": {
            "composite": "GREEN",
            "flags": {
                "availability": "GREEN",
                "lead_time": "GREEN",
                "cost": "GREEN",
                "lifecycle": "GREEN",
                "geopolitical": "YELLOW",
            },
        },
        "substitutes": [
            {
                "mpn": "FTLX8574D3BCL",
                "manufacturer": "Finisar (II-VI)",
                "compatibility_grade": "drop-in",
                "key_differences": "MSA-compliant, identical electrical and optical specifications",
                "why_better": "15% lower price, 8,000+ units in stock at Mouser",
                "estimated_availability": "In stock — ships in 2 weeks",
            },
        ],
    },
    {
        "mpn": "TAS5766MDCA",
        "manufacturer": "Texas Instruments",
        "quantity": 16,
        "reference_designators": ["U10", "U11", "U26"],
        "description": "TAS5766M Smart Amplifier with Integrated DSP, Class-D, 30W BTL, I2S/TDM",
        "distributor_data": {
            "description": "Smart Amplifier with Integrated DSP, 30W Class-D",
            "manufacturer": "Texas Instruments",
            "lifecycle_status": "Active",
            "unit_price": 4.85,
            "stock": 15000,
            "provider": "Mouser Electronics",
            "lead_time_weeks": 2,
            "fab_location": "USA (RFAB Dallas)",
            "datasheet_url": "",
            "geo_risk": "LOW",
        },
        "risk": {
            "composite": "GREEN",
            "flags": {
                "availability": "GREEN",
                "lead_time": "GREEN",
                "cost": "GREEN",
                "lifecycle": "GREEN",
                "geopolitical": "GREEN",
            },
        },
        "substitutes": [],
    },
    {
        "mpn": "VSC8514XKN",
        "manufacturer": "Microchip Technology",
        "quantity": 2,
        "reference_designators": ["PHY1", "PHY2"],
        "description": "VSC8514 Quad-port 10/100/1000BASE-T GbE PHY, QSGMII MAC interface, QFP-128",
        "distributor_data": {
            "description": "4-port GbE PHY with QSGMII interface",
            "manufacturer": "Microsemi / Microchip",
            "lifecycle_status": "Active",
            "unit_price": 14.20,
            "stock": 3200,
            "provider": "Mouser Electronics",
            "lead_time_weeks": 6,
            "fab_location": "USA",
            "datasheet_url": "",
            "geo_risk": "LOW",
        },
        "risk": {
            "composite": "GREEN",
            "flags": {
                "availability": "GREEN",
                "lead_time": "GREEN",
                "cost": "GREEN",
                "lifecycle": "GREEN",
                "geopolitical": "GREEN",
            },
        },
        "substitutes": [],
    },
]


# ─── Helpers ─────────────────────────────────────────────────────────────────
RISK_ICONS = {"RED": "🔴", "YELLOW": "🟡", "GREEN": "🟢"}


def pill(risk: str, label=None) -> str:
    text = label or risk
    return f'<span class="pill pill-{risk}">{text}</span>'


def render_metric_cards(results: list) -> None:
    total = len(results)
    red    = sum(1 for r in results if r["risk"]["composite"] == "RED")
    yellow = sum(1 for r in results if r["risk"]["composite"] == "YELLOW")
    green  = sum(1 for r in results if r["risk"]["composite"] == "GREEN")

    st.markdown(f"""
<div class="metric-row">
  <div class="metric-card">
    <div class="metric-label">Total Parts</div>
    <div class="metric-value">{total}</div>
    <div class="metric-sub">in BOM</div>
  </div>
  <div class="metric-card metric-card-red">
    <div class="metric-label">High Risk</div>
    <div class="metric-value metric-value-red">{red}</div>
    <div class="metric-sub">of {total} parts</div>
  </div>
  <div class="metric-card metric-card-yellow">
    <div class="metric-label">Medium Risk</div>
    <div class="metric-value metric-value-yellow">{yellow}</div>
    <div class="metric-sub">of {total} parts</div>
  </div>
  <div class="metric-card metric-card-green">
    <div class="metric-label">Low Risk</div>
    <div class="metric-value metric-value-green">{green}</div>
    <div class="metric-sub">of {total} parts</div>
  </div>
</div>
""", unsafe_allow_html=True)


def render_risk_strip(flags: dict) -> None:
    dims = [
        ("Availability", "availability"),
        ("Lead Time",    "lead_time"),
        ("Cost",         "cost"),
        ("Lifecycle",    "lifecycle"),
        ("Geo",          "geopolitical"),
    ]
    pills_html = ""
    for label, key in dims:
        risk = flags.get(key, "GREEN")
        pills_html += f"""
<div class="risk-dim">
  <span class="risk-dim-label">{label}</span>
  <span class="pill pill-{risk}">{RISK_ICONS[risk]}&nbsp;{risk}</span>
</div>"""
    st.markdown(f'<div class="risk-strip">{pills_html}</div>', unsafe_allow_html=True)


def render_substitute_card(sub: dict) -> None:
    grade_raw = sub.get("compatibility_grade", "minor-rework").lower()

    if "drop" in grade_raw:
        card_class, grade_label, grade_risk = "sub-drop-in", "DROP-IN", "GREEN"
    elif "redesign" in grade_raw:
        card_class, grade_label, grade_risk = "sub-redesign", "REDESIGN REQ.", "RED"
    else:
        card_class, grade_label, grade_risk = "sub-minor", "MINOR REWORK", "YELLOW"

    mpn  = sub.get("mpn", "")
    mfr  = sub.get("manufacturer", "")
    diff = sub.get("key_differences", "")
    why  = sub.get("why_better", "")
    avail = sub.get("estimated_availability", "")

    st.markdown(f"""
<div class="sub-card {card_class}">
  <div class="sub-header">
    <span class="sub-mpn">{mpn}</span>
    <span class="sub-mfr">{mfr}</span>
    <span class="sub-grade-spacer">{pill(grade_risk, grade_label)}</span>
  </div>
  <div class="sub-diff">📐 {diff}</div>
  <div class="sub-why">✓ {why}</div>
  <div class="sub-avail">📦 {avail}</div>
</div>
""", unsafe_allow_html=True)


def render_part_rows(results: list) -> None:
    sort_order = {"RED": 0, "YELLOW": 1, "GREEN": 2}
    sorted_results = sorted(results, key=lambda r: sort_order[r["risk"]["composite"]])

    for part in sorted_results:
        mpn          = part.get("mpn", "—")
        manufacturer = part.get("manufacturer", "")
        description  = part.get("description", "")
        risk         = part["risk"]["composite"]
        flags        = part["risk"]["flags"]
        dist         = part.get("distributor_data", {})

        price     = dist.get("unit_price")
        stock     = dist.get("stock")
        lead      = dist.get("lead_time_weeks")
        lifecycle = dist.get("lifecycle_status", "—")
        fab       = dist.get("fab_location", "—")
        provider  = dist.get("provider", "—")
        quantity  = part.get("quantity", 1)

        price_str = f"${price:,.2f}" if price is not None else "N/A"
        stock_str = f"{stock:,}"     if stock is not None else "N/A"
        lead_str  = f"{lead}w"       if lead  is not None else "N/A"
        desc_short = description[:70] + ("…" if len(description) > 70 else "")

        # Expander label — markdown supported
        icon = RISK_ICONS[risk]
        label = (
            f"{icon} &nbsp; **`{mpn}`** &nbsp;·&nbsp; {desc_short}"
            f"&nbsp;&nbsp;&nbsp;&nbsp;{price_str} &nbsp;·&nbsp; {lead_str} lead &nbsp;·&nbsp; {stock_str} stk"
        )

        with st.expander(label):
            # Risk breakdown
            st.markdown('<div class="detail-section-header">Risk Breakdown</div>', unsafe_allow_html=True)
            render_risk_strip(flags)

            # Detail grid
            st.markdown(f"""
<div class="detail-section-header">Component Details</div>
<div class="detail-grid">
  <div>
    <div class="detail-row">
      <span class="detail-key">Manufacturer</span>
      <span class="detail-val">{manufacturer}</span>
    </div>
    <div class="detail-row">
      <span class="detail-key">Lifecycle</span>
      <span class="detail-val">{lifecycle}</span>
    </div>
    <div class="detail-row">
      <span class="detail-key">Fab Location</span>
      <span class="detail-val">{fab}</span>
    </div>
    <div class="detail-row">
      <span class="detail-key">Distributor</span>
      <span class="detail-val">{provider}</span>
    </div>
  </div>
  <div>
    <div class="detail-row">
      <span class="detail-key">Unit Price</span>
      <span class="detail-val">{price_str}</span>
    </div>
    <div class="detail-row">
      <span class="detail-key">In Stock</span>
      <span class="detail-val">{stock_str}</span>
    </div>
    <div class="detail-row">
      <span class="detail-key">Lead Time</span>
      <span class="detail-val">{lead_str}</span>
    </div>
    <div class="detail-row">
      <span class="detail-key">Qty Needed</span>
      <span class="detail-val">{quantity}</span>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

            if description:
                st.markdown(
                    f'<p style="color:var(--text-secondary);font-size:0.8rem;margin:14px 0;line-height:1.6;">{description}</p>',
                    unsafe_allow_html=True,
                )

            # Substitutes
            subs = part.get("substitutes", [])
            if subs:
                st.markdown(
                    '<div class="detail-section-header">Suggested Alternatives</div>',
                    unsafe_allow_html=True,
                )
                for sub in subs:
                    render_substitute_card(sub)


def build_excel(results: list) -> bytes:
    rows = []
    for r in results:
        dist = r.get("distributor_data", {})
        flags = r["risk"]["flags"]
        rows.append({
            "MPN":              r.get("mpn", ""),
            "Manufacturer":     r.get("manufacturer", ""),
            "Description":      r.get("description", ""),
            "Quantity":         r.get("quantity", ""),
            "Risk":             r["risk"]["composite"],
            "Availability":     flags.get("availability", ""),
            "Lead Time Risk":   flags.get("lead_time", ""),
            "Cost Risk":        flags.get("cost", ""),
            "Lifecycle Risk":   flags.get("lifecycle", ""),
            "Geo Risk":         flags.get("geopolitical", ""),
            "Unit Price ($)":   dist.get("unit_price", ""),
            "Stock":            dist.get("stock", ""),
            "Lead Time (wk)":   dist.get("lead_time_weeks", ""),
            "Lifecycle Status": dist.get("lifecycle_status", ""),
            "Fab Location":     dist.get("fab_location", ""),
            "Distributor":      dist.get("provider", ""),
            "Substitutes":      ", ".join(
                s.get("mpn", "") for s in r.get("substitutes", [])
            ),
        })
    df = pd.DataFrame(rows)
    buf = io.BytesIO()
    try:
        df.to_excel(buf, index=False, engine="openpyxl")
    except Exception:
        df.to_csv(buf, index=False)
    buf.seek(0)
    return buf.read()


def build_text_report(results: list) -> bytes:
    lines = [
        "SupplyLine — Supply Chain Risk Report",
        "=" * 60,
        "",
    ]
    for r in results:
        risk  = r["risk"]["composite"]
        flags = r["risk"]["flags"]
        dist  = r.get("distributor_data", {})
        lines += [
            f"[{risk}]  {r.get('mpn', '')}  —  {r.get('manufacturer', '')}",
            f"       {r.get('description', '')}",
            f"       Price: ${dist.get('unit_price', 'N/A')}  |  Stock: {dist.get('stock', 'N/A')}  |  Lead: {dist.get('lead_time_weeks', 'N/A')}w",
            f"       Flags: " + "  ".join(
                f"{k.upper()}:{v}" for k, v in flags.items()
            ),
        ]
        subs = r.get("substitutes", [])
        if subs:
            lines.append("       Alternatives: " + ", ".join(s["mpn"] for s in subs))
        lines.append("")
    return "\n".join(lines).encode()


# ─── Sidebar ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
<div class="sidebar-logo">
  <div class="sidebar-logo-title">⚡ SupplyLine</div>
  <div class="sidebar-logo-caption">Design-time supply chain intelligence</div>
</div>
""", unsafe_allow_html=True)

    st.markdown('<div class="sidebar-section">Risk Thresholds</div>', unsafe_allow_html=True)
    lead_red   = st.number_input("Lead time RED (weeks)",    value=16, min_value=1,  max_value=52,  step=1)
    lead_yel   = st.number_input("Lead time YELLOW (weeks)", value=8,  min_value=1,  max_value=52,  step=1)
    stock_min  = st.number_input("Min acceptable stock",     value=100, min_value=0, max_value=10000, step=10)
    price_spike = st.number_input("Price spike threshold (%)", value=30, min_value=0, max_value=200,  step=5)

    st.markdown('<div class="sidebar-section">Filters</div>', unsafe_allow_html=True)
    show_red    = st.toggle("Show HIGH RISK (RED)",    value=True)
    show_yellow = st.toggle("Show MEDIUM RISK (YELLOW)", value=True)
    show_green  = st.toggle("Show LOW RISK (GREEN)",   value=True)

    st.markdown('<div class="sidebar-section">Resources</div>', unsafe_allow_html=True)
    st.download_button(
        "📥 Download Sample BOM",
        data=SAMPLE_BOM_CSV.encode(),
        file_name="sample_bom.csv",
        mime="text/csv",
        use_container_width=True,
    )
    st.markdown(
        '<p style="font-size:0.7rem; color:var(--text-muted); margin-top:8px; font-weight:500;">CSV format · MPN, Manufacturer,<br>Quantity, Reference Designators</p>',
        unsafe_allow_html=True,
    )


# ─── Main ────────────────────────────────────────────────────────────────────
inject_css()

st.markdown("""
<div class="app-hero">
  <h1>⚡ SupplyLine</h1>
  <p>Design-Time Supply Chain Intelligence for Photonics OEMs</p>
</div>
""", unsafe_allow_html=True)

# ── Upload row ────────────────────────────────────────────────────────────────
col_upload, col_sample, col_analyze = st.columns([4, 1.4, 1.8])

with col_upload:
    uploaded_file = st.file_uploader(
        "Upload BOM",
        type=["csv", "xlsx"],
        label_visibility="collapsed",
        help="Upload a CSV or Excel BOM file to analyze",
    )

with col_sample:
    sample_clicked = st.button("Try Sample BOM", use_container_width=True)

with col_analyze:
    analyze_clicked = st.button(
        "⚡ Analyze with Claude",
        use_container_width=True,
        type="primary",
    )

# ── Session state ─────────────────────────────────────────────────────────────
if "results" not in st.session_state:
    st.session_state.results = None

# ── Trigger logic ─────────────────────────────────────────────────────────────
if sample_clicked:
    st.session_state.results = SAMPLE_RESULTS

if analyze_clicked:
    if uploaded_file is None:
        st.warning("Upload a BOM file first, or click **Try Sample BOM** to run the demo.")
    elif BACKEND_AVAILABLE:
        with st.spinner("Analyzing BOM with Claude…"):
            try:
                st.session_state.results = analyze_bom(uploaded_file)
            except Exception as exc:
                st.error(f"Analysis failed: {exc}")
                st.session_state.results = SAMPLE_RESULTS
    else:
        st.info("Backend not connected — showing sample analysis.")
        st.session_state.results = SAMPLE_RESULTS

# ── Results ──────────────────────────────────────────────────────────────────
if st.session_state.results:
    results = st.session_state.results

    # Apply filters
    filtered = [
        r for r in results
        if (r["risk"]["composite"] == "RED"    and show_red)
        or (r["risk"]["composite"] == "YELLOW" and show_yellow)
        or (r["risk"]["composite"] == "GREEN"  and show_green)
    ]

    # Metric cards
    render_metric_cards(results)

    # Download row
    col_dl1, col_dl2, _ = st.columns([1.5, 1.5, 4])
    with col_dl1:
        st.download_button(
            "📊 Annotated BOM (Excel)",
            data=build_excel(results),
            file_name="supplyline_annotated_bom.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with col_dl2:
        st.download_button(
            "📄 Risk Report (TXT)",
            data=build_text_report(results),
            file_name="supplyline_risk_report.txt",
            mime="text/plain",
            use_container_width=True,
        )

    st.markdown("<hr/>", unsafe_allow_html=True)

    # Parts header
    n = len(filtered)
    st.markdown(
        f'<div style="font-size:0.65rem;letter-spacing:0.10em;text-transform:uppercase;color:var(--text-muted);font-weight:700;margin-bottom:12px;">'
        f'{n} Part{"s" if n != 1 else ""} · Click to expand details</div>',
        unsafe_allow_html=True,
    )

    if filtered:
        render_part_rows(filtered)
    else:
        st.markdown(
            '<div class="empty-state"><div class="empty-state-icon">🔍</div>'
            '<div class="empty-state-text">No parts match the current filters.</div></div>',
            unsafe_allow_html=True,
        )

else:
    # Empty / landing state
    st.markdown("""
<div class="empty-state">
  <div class="empty-state-icon">🔍</div>
  <div class="empty-state-text">
    Upload a BOM CSV or click <strong style="color:var(--accent);">Try Sample BOM</strong>
    to see design-time supply chain risk analysis.
  </div>
</div>
""", unsafe_allow_html=True)
