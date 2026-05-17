"""
SupplyLine — Design-Time Supply Chain Intelligence for Photonics OEMs
"""

import io
import sys
from pathlib import Path

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

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
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* ── App shell ── */
.stApp {
    background-color: #09090b;
    color: #fafafa;
}
.main .block-container {
    padding-top: 2rem;
    padding-bottom: 4rem;
    max-width: 1200px;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background-color: #09090b !important;
    border-right: 1px solid #27272a !important;
}
section[data-testid="stSidebar"] > div {
    background-color: #09090b !important;
    padding-top: 1.5rem;
}

/* ── Typography ── */
h1, h2, h3 {
    font-weight: 700 !important;
    letter-spacing: -0.02em !important;
    color: #fafafa !important;
}
p, li { color: #a1a1aa; font-size: 0.875rem; }
label, .stTextInput label, .stNumberInput label, .stSelectbox label {
    color: #52525b !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}

/* ── Sidebar components ── */
.sidebar-logo {
    padding-bottom: 16px;
    border-bottom: 1px solid #27272a;
    margin-bottom: 20px;
}
.sidebar-logo-title {
    font-size: 1.1rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    background: linear-gradient(90deg, #fafafa 55%, #a78bfa);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    display: inline-block;
}
.sidebar-logo-caption {
    font-size: 0.72rem;
    color: #52525b;
    margin-top: 3px;
}
.sidebar-section {
    font-size: 0.7rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #52525b;
    margin-top: 20px;
    margin-bottom: 10px;
    padding-bottom: 4px;
    border-bottom: 1px solid #27272a;
}

/* ── Metric cards ── */
.metric-row {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 12px;
    margin-bottom: 28px;
}
.metric-card {
    background: #18181b;
    border: 1px solid #27272a;
    border-radius: 8px;
    padding: 16px 20px;
    transition: transform 0.18s ease, border-color 0.2s ease, box-shadow 0.2s ease;
    cursor: default;
}
.metric-card-red   { border-color: rgba(239,68,68,0.4); }
.metric-card-yellow{ border-color: rgba(234,179,8,0.4); }
.metric-card-green { border-color: rgba(34,197,94,0.4); }
.metric-label {
    font-size: 0.7rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #52525b;
    margin-bottom: 8px;
}
.metric-value {
    font-size: 2rem;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #fafafa;
    line-height: 1;
    margin-bottom: 4px;
}
.metric-value-red    { color: #f87171; }
.metric-value-yellow { color: #facc15; }
.metric-value-green  { color: #4ade80; }
.metric-sub {
    font-size: 0.72rem;
    color: #52525b;
}

/* ── Risk pills ── */
.pill {
    display: inline-block;
    border-radius: 9999px;
    padding: 2px 10px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    border: 1px solid;
    white-space: nowrap;
}
.pill-RED    { background: rgba(239,68,68,0.12);  border-color: rgba(239,68,68,0.4);  color: #f87171; }
.pill-YELLOW { background: rgba(234,179,8,0.12);  border-color: rgba(234,179,8,0.4);  color: #facc15; }
.pill-GREEN  { background: rgba(34,197,94,0.12);  border-color: rgba(34,197,94,0.4);  color: #4ade80; }

/* ── Risk dot ── */
.risk-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    flex-shrink: 0;
}
.dot-RED    { background: #f87171; animation: pulse-ring 2.2s ease-out infinite; }
.dot-YELLOW { background: #facc15; }
.dot-GREEN  { background: #4ade80; }

/* ── Part card header (inside expander summary) ── */
.part-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    width: 100%;
    gap: 12px;
}
.part-header-left {
    display: flex;
    align-items: center;
    gap: 10px;
    min-width: 0;
}
.part-mpn {
    font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
    font-size: 0.875rem;
    font-weight: 600;
    color: #fafafa;
    white-space: nowrap;
}
.part-desc {
    font-size: 0.78rem;
    color: #71717a;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 380px;
}
.part-header-right {
    display: flex;
    align-items: center;
    gap: 16px;
    flex-shrink: 0;
}
.stat-block { text-align: right; }
.stat-label {
    font-size: 0.62rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #52525b;
    display: block;
}
.stat-value {
    font-size: 0.78rem;
    color: #a1a1aa;
    display: block;
}

/* ── Risk breakdown strip ── */
.risk-strip {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
    margin: 8px 0 16px 0;
}
.risk-dim {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
}
.risk-dim-label {
    font-size: 0.62rem;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #52525b;
}

/* ── Detail section inside expander ── */
.detail-section-header {
    font-size: 0.65rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #52525b;
    margin-bottom: 8px;
    margin-top: 16px;
    padding-bottom: 6px;
    border-bottom: 1px solid #27272a;
}
.detail-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0 32px;
}
.detail-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 0;
    border-bottom: 1px solid #27272a;
}
.detail-key {
    font-size: 0.72rem;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    color: #52525b;
}
.detail-val {
    font-size: 0.8rem;
    color: #a1a1aa;
    text-align: right;
}

/* ── Substitute cards ── */
.sub-card {
    background: #09090b;
    border: 1px solid #27272a;
    border-radius: 6px;
    padding: 12px 16px;
    margin-bottom: 8px;
}
.sub-drop-in  { border-left: 3px solid #4ade80; }
.sub-minor    { border-left: 3px solid #facc15; }
.sub-redesign { border-left: 3px solid #f87171; }
.sub-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 6px;
}
.sub-mpn {
    font-family: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;
    font-weight: 700;
    font-size: 0.875rem;
    color: #fafafa;
}
.sub-mfr {
    font-size: 0.75rem;
    color: #71717a;
}
.sub-grade-spacer { margin-left: auto; }
.sub-diff  { font-size: 0.78rem; color: #a1a1aa; margin-top: 4px; }
.sub-why   { font-size: 0.78rem; color: #d4d4d8; margin-top: 4px; }
.sub-avail { font-size: 0.75rem; color: #52525b;  margin-top: 4px; }

/* ── Expander dark overrides ── */
[data-testid="stExpander"] {
    background: #18181b !important;
    border: 1px solid #27272a !important;
    border-radius: 8px !important;
    margin-bottom: 4px !important;
    overflow: hidden;
}
[data-testid="stExpander"] > details {
    background: #18181b !important;
}
[data-testid="stExpander"] summary {
    color: #fafafa !important;
    background: #18181b !important;
    padding: 12px 16px !important;
}
[data-testid="stExpander"] summary:hover {
    background: #1f1f23 !important;
}
[data-testid="stExpander"] summary svg {
    fill: #52525b !important;
}
[data-testid="stExpander"] > details > div {
    background: #18181b !important;
    border-top: 1px solid #27272a !important;
    padding: 16px !important;
}
[data-testid="stExpander"]:hover {
    border-color: #3f3f46 !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: #18181b;
    border: 1px dashed #27272a;
    border-radius: 8px;
    padding: 8px;
}
[data-testid="stFileUploader"] > div {
    background: transparent !important;
}
[data-testid="stFileUploadDropzone"] {
    background: #18181b !important;
    border: 1px dashed #27272a !important;
    border-radius: 8px !important;
}
[data-testid="stFileUploadDropzone"]:hover {
    border-color: #8b5cf6 !important;
    background: rgba(139,92,246,0.04) !important;
}
[data-testid="stFileUploadDropzone"] p,
[data-testid="stFileUploadDropzone"] span {
    color: #71717a !important;
}

/* ── Buttons ── */
.stButton > button {
    background: transparent !important;
    border: 1px solid #27272a !important;
    color: #fafafa !important;
    border-radius: 6px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.875rem !important;
    font-weight: 400 !important;
    transition: border-color 0.15s, background 0.15s !important;
}
.stButton > button:hover {
    background: #18181b !important;
    border-color: #3f3f46 !important;
    color: #fafafa !important;
}
[data-testid="baseButton-primary"] {
    background: #8b5cf6 !important;
    border: none !important;
    color: #ffffff !important;
    font-weight: 600 !important;
    border-radius: 6px !important;
}
[data-testid="baseButton-primary"]:hover {
    background: #7c3aed !important;
    border: none !important;
    color: #ffffff !important;
}

/* ── Download buttons ── */
[data-testid="stDownloadButton"] button {
    background: transparent !important;
    border: 1px solid #27272a !important;
    color: #a1a1aa !important;
    border-radius: 6px !important;
    font-size: 0.8rem !important;
}
[data-testid="stDownloadButton"] button:hover {
    border-color: #3f3f46 !important;
    background: #18181b !important;
    color: #fafafa !important;
}

/* ── Inputs ── */
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"]   input {
    background: #18181b !important;
    border: 1px solid #27272a !important;
    color: #fafafa !important;
    border-radius: 6px !important;
}
[data-testid="stNumberInput"] > div,
[data-testid="stTextInput"]   > div {
    background: #18181b !important;
    border-color: #27272a !important;
}

/* ── Toggles ── */
[data-testid="stToggle"] span[data-checked="true"] {
    background: #8b5cf6 !important;
}

/* ── Alerts ── */
[data-testid="stInfo"] {
    background: rgba(139,92,246,0.1) !important;
    border: 1px solid rgba(139,92,246,0.3) !important;
    color: #c4b5fd !important;
    border-radius: 6px !important;
}
[data-testid="stWarning"] {
    background: rgba(234,179,8,0.1) !important;
    border: 1px solid rgba(234,179,8,0.3) !important;
    border-radius: 6px !important;
}
[data-testid="stError"] {
    background: rgba(239,68,68,0.1) !important;
    border: 1px solid rgba(239,68,68,0.3) !important;
    border-radius: 6px !important;
}

/* ── Dividers ── */
hr { border-color: #27272a !important; margin: 20px 0 !important; }

/* ── Empty state ── */
.empty-state {
    text-align: center;
    padding: 80px 20px;
    color: #3f3f46;
}
.empty-state-icon { font-size: 2.5rem; margin-bottom: 16px; }
.empty-state-text { font-size: 0.9rem; color: #52525b; }

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: #09090b; }
::-webkit-scrollbar-thumb { background: #27272a; border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: #3f3f46; }

/* ── Animations ── */
@keyframes pulse-ring {
    0%   { box-shadow: 0 0 0 0   rgba(248,113,113,0.55); }
    70%  { box-shadow: 0 0 0 7px rgba(248,113,113,0); }
    100% { box-shadow: 0 0 0 0   rgba(248,113,113,0); }
}
@keyframes gradient-x {
    0%, 100% { background-position: 0%   50%; }
    50%       { background-position: 100% 50%; }
}
@keyframes fade-in-up {
    from { opacity: 0; transform: translateY(6px); }
    to   { opacity: 1; transform: translateY(0);   }
}
@keyframes word-rotate {
    0%   { opacity: 0; transform: translateY(8px);  }
    3%   { opacity: 1; transform: translateY(0);    }
    17%  { opacity: 1; transform: translateY(0);    }
    23%  { opacity: 0; transform: translateY(-8px); }
    100% { opacity: 0; transform: translateY(8px);  }
}

/* ── Animated gradient accent bar ── */
.gradient-line {
    height: 1px;
    background: linear-gradient(90deg, transparent, #6d28d9, #a78bfa, #6d28d9, transparent);
    background-size: 200% 100%;
    animation: gradient-x 5s linear infinite;
    margin: 14px 0 22px;
    border-radius: 1px;
}

/* ── Hero section ── */
.hero-title {
    font-size: 1.9rem !important;
    font-weight: 800 !important;
    letter-spacing: -0.03em !important;
    color: #fafafa !important;
    margin: 0 0 5px !important;
    line-height: 1.2 !important;
}
.hero-sub {
    font-size: 0.875rem;
    color: #71717a;
    margin: 0;
    display: flex;
    align-items: baseline;
    flex-wrap: nowrap;
    gap: 0;
}
.rotating-container {
    display: inline-block;
    position: relative;
    height: 1.2em;
    overflow: hidden;
    vertical-align: bottom;
    min-width: 78px;
    margin-left: 4px;
}
.rword {
    display: block;
    position: absolute;
    left: 0;
    top: 0;
    color: #a78bfa;
    font-weight: 600;
    opacity: 0;
    transform: translateY(8px);
    animation: word-rotate 10s infinite;
    animation-fill-mode: backwards;
    white-space: nowrap;
}
.rword:nth-child(1) { animation-delay: 0s;  }
.rword:nth-child(2) { animation-delay: 2s;  }
.rword:nth-child(3) { animation-delay: 4s;  }
.rword:nth-child(4) { animation-delay: 6s;  }
.rword:nth-child(5) { animation-delay: 8s;  }

/* ── Metric card hover glow ── */
.metric-card:hover                { transform: translateY(-2px); }
.metric-card-red:hover    { box-shadow: 0 8px 28px rgba(248,113,113,0.2);  border-color: rgba(248,113,113,0.65) !important; }
.metric-card-yellow:hover { box-shadow: 0 8px 28px rgba(250,204,21,0.16);  border-color: rgba(250,204,21,0.65)  !important; }
.metric-card-green:hover  { box-shadow: 0 8px 28px rgba(74,222,128,0.16);  border-color: rgba(74,222,128,0.65)  !important; }

/* ── Substitute card hover ── */
.sub-card {
    transition: transform 0.15s ease, box-shadow 0.15s ease, border-color 0.15s ease;
}
.sub-card:hover { transform: translateY(-1px); box-shadow: 0 4px 16px rgba(0,0,0,0.4); }
.sub-drop-in:hover  { border-left-color: #86efac; }
.sub-minor:hover    { border-left-color: #fde047; }
.sub-redesign:hover { border-left-color: #fca5a5; }

/* ── Parts list fade-in ── */
[data-testid="stExpander"] { animation: fade-in-up 0.28s ease-out both; }

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
                    f'<p style="color:#71717a;font-size:0.78rem;margin:12px 0;">{description}</p>',
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


# ─── Feature section (empty-state landing) ───────────────────────────────────
def render_feature_section() -> None:
    """Tabbed feature showcase rendered via components.html — shown on landing state."""
    html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
  *, *::before, *::after { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; background: #09090b;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; color: #fafafa; }

  .section  { padding: 40px 0 8px; }
  .container { max-width: 100%; padding: 0 4px; }

  /* ── Badge ── */
  .badge {
    display: inline-flex; align-items: center; border-radius: 9999px;
    border: 1px solid #3f3f46; padding: 3px 12px;
    font-size: 0.68rem; font-weight: 600; color: #71717a;
    letter-spacing: 0.07em; text-transform: uppercase;
  }

  /* ── Section header ── */
  .section-header {
    display: flex; flex-direction: column; align-items: center;
    gap: 14px; text-align: center; margin-bottom: 36px;
  }
  .section-header h1 {
    font-size: 1.75rem; font-weight: 700; letter-spacing: -0.03em;
    color: #fafafa; max-width: 540px; line-height: 1.25; margin: 0;
  }
  .section-header p {
    color: #71717a; font-size: 0.875rem; max-width: 460px;
    line-height: 1.6; margin: 0;
  }

  /* ── Tab list ── */
  .tabs-list {
    display: flex; justify-content: center; gap: 6px;
    margin-bottom: 20px; flex-wrap: wrap;
  }
  .tab-btn {
    display: flex; align-items: center; gap: 7px;
    padding: 9px 18px; border-radius: 12px; border: none;
    background: transparent; color: #52525b;
    font-size: 0.825rem; font-weight: 600; cursor: pointer;
    transition: background 0.15s, color 0.15s;
    font-family: 'Inter', sans-serif; outline: none;
  }
  .tab-btn:hover { background: #1c1c1f; color: #a1a1aa; }
  .tab-btn.active { background: #1c1c1f; color: #fafafa; }
  .tab-btn svg { width: 15px; height: 15px; flex-shrink: 0; }

  /* ── Content box ── */
  .tabs-content {
    background: #18181b; border: 1px solid #27272a;
    border-radius: 20px; padding: 40px;
  }

  /* ── Panels ── */
  .tab-panel {
    display: none; grid-template-columns: 1fr 1fr;
    gap: 48px; align-items: center;
  }
  .tab-panel.active {
    display: grid;
    animation: panel-in 0.22s ease-out both;
  }
  @keyframes panel-in {
    from { opacity: 0; transform: translateY(7px); }
    to   { opacity: 1; transform: translateY(0);   }
  }

  /* ── Panel text ── */
  .panel-text { display: flex; flex-direction: column; gap: 16px; }
  .panel-badge {
    display: inline-flex; align-items: center; border-radius: 9999px;
    border: 1px solid #3f3f46; padding: 3px 12px;
    font-size: 0.68rem; font-weight: 600; color: #71717a;
    background: #09090b; letter-spacing: 0.07em;
    text-transform: uppercase; width: fit-content;
  }
  .panel-title {
    font-size: 1.65rem; font-weight: 700; letter-spacing: -0.025em;
    color: #fafafa; line-height: 1.2; margin: 0;
  }
  .panel-desc {
    color: #71717a; line-height: 1.65;
    font-size: 0.875rem; margin: 0;
  }
  .panel-btn {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 10px 22px; background: #8b5cf6; color: #fff;
    border-radius: 8px; border: none; font-size: 0.875rem;
    font-weight: 500; cursor: pointer; width: fit-content;
    margin-top: 6px; font-family: 'Inter', sans-serif;
    transition: background 0.15s; text-decoration: none;
  }
  .panel-btn:hover { background: #7c3aed; }

  /* ── Panel image ── */
  .panel-img {
    border-radius: 14px; width: 100%; aspect-ratio: 4/3;
    object-fit: cover; border: 1px solid #27272a;
    display: block;
  }
</style>
</head>
<body>
<section class="section">
  <div class="container">

    <div class="section-header">
      <span class="badge">SupplyLine</span>
      <h1>Design-time intelligence for every line of your BOM.</h1>
      <p>From photonics PICs to passive components — know your supply chain risk before you're committed to a design.</p>
    </div>

    <div class="tabs-list">
      <button class="tab-btn active" onclick="switchTab(event,'risk')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
        </svg>
        Risk Analysis
      </button>
      <button class="tab-btn" onclick="switchTab(event,'avl')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
        </svg>
        AVL Intelligence
      </button>
      <button class="tab-btn" onclick="switchTab(event,'sub')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <line x1="6" y1="3" x2="6" y2="15"/>
          <circle cx="18" cy="6" r="3"/>
          <circle cx="6" cy="18" r="3"/>
          <path d="M18 9a9 9 0 0 1-9 9"/>
        </svg>
        Substitution Engine
      </button>
    </div>

    <div class="tabs-content">

      <!-- Risk Analysis -->
      <div id="panel-risk" class="tab-panel active">
        <div class="panel-text">
          <span class="panel-badge">AI-Powered</span>
          <h3 class="panel-title">Catch 60-week lead times before you're locked in.</h3>
          <p class="panel-desc">Claude analyzes every line of your BOM across six risk dimensions — availability, lead time, cost, lifecycle, geopolitical exposure, and vendor concentration — in seconds. No surprises at procurement.</p>
          <button class="panel-btn">Analyze a BOM &rarr;</button>
        </div>
        <img class="panel-img"
          src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=700&q=80"
          alt="Supply chain risk analytics dashboard" loading="lazy"/>
      </div>

      <!-- AVL Intelligence -->
      <div id="panel-avl" class="tab-panel">
        <div class="panel-text">
          <span class="panel-badge">Supplier Aware</span>
          <h3 class="panel-title">Know your AVL gaps before qualification starts.</h3>
          <p class="panel-desc">SupplyLine cross-references your BOM against your Approved Vendor List, surfaces coverage gaps, and flags customer flow-down restrictions — Verizon, AT&T, DoD — that would otherwise surface at contract review.</p>
          <button class="panel-btn">Upload Your AVL &rarr;</button>
        </div>
        <img class="panel-img"
          src="https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=700&q=80"
          alt="Network and supply chain visualization" loading="lazy"/>
      </div>

      <!-- Substitution Engine -->
      <div id="panel-sub" class="tab-panel">
        <div class="panel-text">
          <span class="panel-badge">Design-Time</span>
          <h3 class="panel-title">Find a drop-in before the shortage hits.</h3>
          <p class="panel-desc">When a part flags RED, SupplyLine surfaces qualified alternatives ranked by compatibility — drop-in, minor rework, or redesign — alongside availability windows and AVL qualification status. Act at design-time, not crunch-time.</p>
          <button class="panel-btn">See Alternatives &rarr;</button>
        </div>
        <img class="panel-img"
          src="https://images.unsplash.com/photo-1518770660439-4636190af475?w=700&q=80"
          alt="Electronic and photonic circuit components" loading="lazy"/>
      </div>

    </div>
  </div>
</section>

<script>
  function switchTab(event, tabId) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => {
      p.classList.remove('active');
      p.style.animation = 'none';
    });
    event.currentTarget.classList.add('active');
    const panel = document.getElementById('panel-' + tabId);
    panel.offsetHeight; // force reflow before re-adding class
    panel.style.animation = '';
    panel.classList.add('active');
  }
</script>
</body>
</html>"""
    components.html(html, height=660, scrolling=False)


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
        '<p style="font-size:0.7rem; color:#52525b; margin-top:8px;">CSV format · MPN, Manufacturer,<br>Quantity, Reference Designators</p>',
        unsafe_allow_html=True,
    )


# ─── Main ────────────────────────────────────────────────────────────────────
inject_css()

st.markdown("""
<div style="margin-bottom:0;">
  <h1 class="hero-title">⚡ SupplyLine</h1>
  <p class="hero-sub">Design-time risk intelligence&nbsp;&mdash;&nbsp;<span class="rotating-container"><span class="rword">faster.</span><span class="rword">smarter.</span><span class="rword">clearer.</span><span class="rword">earlier.</span><span class="rword">safer.</span></span></p>
  <div class="gradient-line"></div>
</div>
""", unsafe_allow_html=True)

# ── Upload row ────────────────────────────────────────────────────────────────
col_upload, col_sample, col_demo, col_analyze = st.columns([4, 1.2, 1.2, 1.6])

with col_upload:
    uploaded_file = st.file_uploader(
        "Upload BOM",
        type=["csv", "xlsx"],
        label_visibility="collapsed",
        help="Upload a CSV or Excel BOM file to analyze",
    )

with col_sample:
    sample_clicked = st.button("Try Sample BOM", use_container_width=True)

with col_demo:
    demo_clicked = st.button("Demo Mode", use_container_width=True)

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
if sample_clicked or demo_clicked:
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
        f'<div style="font-size:0.7rem;letter-spacing:0.08em;text-transform:uppercase;color:#52525b;margin-bottom:10px;">'
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
    # Landing state — feature showcase
    render_feature_section()
