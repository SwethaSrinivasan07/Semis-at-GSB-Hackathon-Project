"""
Catena — Design-Time Supply Chain Intelligence for Photonics OEMs
"""

import base64
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
# Use the bundled brand logo as the browser-tab favicon if available;
# otherwise fall back to the lightning-bolt emoji.
_assets_dir = Path(__file__).parent / "assets"
_favicon_path = next(
    (p for p in (_assets_dir / n for n in
                 ("logo 2.jpeg", "logo 2.jpg", "logo 2.png",
                  "logo.jpeg", "logo.jpg", "logo.png", "logo.webp"))
     if p.exists()),
    None,
)
st.set_page_config(
    page_title="Catena",
    page_icon=str(_favicon_path) if _favicon_path else "⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─── CSS ─────────────────────────────────────────────────────────────────────
def inject_css():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

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
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
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
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
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
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
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
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
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

/* ── Component image (top of expanded part card) ── */
.part-image {
    display: block;
    width: 100%;
    max-height: 180px;
    object-fit: cover;
    border-radius: 12px;
    border: 1px solid var(--border);
    box-shadow: 0 4px 14px rgba(15,23,42,0.05);
    margin: 4px 0 18px;
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
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
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
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
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
    font-family: 'Inter', system-ui, -apple-system, sans-serif !important;
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

/* ── Hide sidebar — replaced by top navbar ── */
[data-testid="stSidebar"],
[data-testid="collapsedControl"] { display: none !important; }

/* ── Bump content below fixed navbar (88px tall now) ── */
.main .block-container { padding-top: 7rem !important; }

/* ══════════════════════════════════════════
   NAVBAR (Navbar1 port — light theme)
═══════════════════════════════════════════ */
.sl-nav {
    position: fixed; top: 0; left: 0; right: 0; z-index: 9999;
    /* Taller than typical so the full Catena logo (C-mark + stylized
       wordmark + tagline) renders legibly on the right side. */
    height: 88px;
    background: rgba(255,255,255,0.96);
    backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px);
    border-bottom: 1px solid rgba(37,99,235,0.10);
    box-shadow: 0 1px 8px rgba(15,23,42,0.06);
    /* flex-end keeps the logo on the right; the menu is absolute-centered
       independently (see .sl-menu rule below). */
    display: flex; align-items: center; justify-content: flex-end;
    padding: 0 28px;
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
}
.sl-nav a, .sl-nav a:hover, .sl-nav a:focus, .sl-nav a:visited,
.sl-nav span, .sl-nav div { text-decoration: none !important; }
/* Top-right brand logo — full composite image (icon + stylized "CATENA"
   wordmark + tagline). Clickable target returns to the home view. */
.sl-logo { display: flex; align-items: center; flex-shrink: 0; }
.sl-logo-img {
    height: 80px; width: 80px;
    object-fit: contain;
    display: block;
    pointer-events: none;
    -webkit-user-drag: none;
}
/* Menu absolute-centered within the navbar so it stays in the middle of
   the viewport regardless of how much space the logo on the right takes. */
.sl-menu {
    position: absolute;
    left: 50%;
    top: 50%;
    transform: translate(-50%, -50%);
    display: flex; align-items: center; gap: 1px;
    list-style: none; margin: 0; padding: 0;
}
.sl-item { position: relative; }
.sl-link {
    display: flex; align-items: center; gap: 4px; padding: 6px 13px; border-radius: 8px;
    font-size: 0.85rem; font-weight: 500; color: #64748B;
    text-decoration: none; cursor: pointer; white-space: nowrap;
    transition: background 0.14s, color 0.14s;
    background: none; border: none; font-family: 'Inter', system-ui, -apple-system, sans-serif;
}
.sl-link:hover, .sl-item:hover > .sl-link { background: #F1F5F9; color: #0F172A; }
.sl-chevron { width: 12px; height: 12px; opacity: 0.45; transition: transform 0.2s, opacity 0.2s; }
.sl-item:hover .sl-chevron { transform: rotate(180deg); opacity: 0.75; }
.sl-drop {
    display: none; position: absolute; top: calc(100% + 10px); left: 0;
    min-width: 278px; background: #FFFFFF;
    border: 1px solid rgba(37,99,235,0.12); border-radius: 14px; padding: 6px;
    box-shadow: 0 16px 48px rgba(15,23,42,0.12); z-index: 100;
}
.sl-item:hover .sl-drop { display: block; }
.sl-drop-item {
    display: flex; align-items: flex-start; gap: 12px;
    padding: 10px 11px; border-radius: 9px; text-decoration: none; transition: background 0.12s;
}
.sl-drop-item:hover { background: #F8FAFF; }
.sl-drop-icon {
    width: 34px; height: 34px; flex-shrink: 0;
    background: #EFF6FF; border: 1px solid rgba(37,99,235,0.15); border-radius: 8px;
    display: flex; align-items: center; justify-content: center; color: #2563EB;
}
.sl-drop-icon svg { width: 15px; height: 15px; }
.sl-drop-title { font-size: 0.82rem; font-weight: 600; color: #0F172A; margin-bottom: 2px; }
.sl-drop-desc  { font-size: 0.73rem; color: #64748B; line-height: 1.4; }
.sl-auth { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.sl-btn-out {
    padding: 7px 14px; border-radius: 8px; border: 1px solid rgba(37,99,235,0.22);
    background: transparent; color: #475569; font-size: 0.83rem; font-weight: 500;
    cursor: pointer; font-family: 'Inter', system-ui, -apple-system, sans-serif;
    transition: all 0.14s; text-decoration: none; white-space: nowrap;
}
.sl-btn-out:hover { border-color: #2563EB; color: #2563EB; background: #EFF6FF; }
.sl-btn-pri {
    padding: 7px 14px; border-radius: 8px; border: 1px solid rgba(37,99,235,0.22);
    background: transparent; color: #475569; font-size: 0.83rem; font-weight: 500;
    cursor: pointer; font-family: 'Inter', system-ui, -apple-system, sans-serif;
    transition: all 0.14s; text-decoration: none; white-space: nowrap;
}
.sl-btn-pri:hover { border-color: #2563EB; color: #2563EB; background: #EFF6FF; }
@media (max-width: 820px) { .sl-menu, .sl-auth { display: none; } }
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


# ─── Component imagery ──────────────────────────────────────────────────────
# Picks a thematically-appropriate stock photo for each part based on simple
# keyword matching against MPN + description. Images are visual context only
# (per the brief: "does not need to match 100%"), served from Unsplash CDN
# with auto-format & crop so they're light and consistent.
# Curated Unsplash pool — hand-verified semiconductor / photonics / networking
# photos only. Kept intentionally small so every image is on-topic; MPNs share.
_IMG = "https://images.unsplash.com/{pid}?auto=format&fit=crop&w=640&q=70"
_PART_IMAGE_POOL = [
    # 0  Adi Goldstein: green PCB with Apple-style chip — most-cited
    #    semiconductor stock photo on Unsplash. Use for IC/SoC/ASIC parts.
    _IMG.format(pid="photo-1518770660439-4636190af475"),
    # 1  Compare Fibre: bundle of yellow single-mode fiber strands — the
    #    canonical fiber-optics stock photo. Use for photonic parts.
    _IMG.format(pid="photo-1558494949-ef010cbdcc31"),
    # 2  Vishnu Mohanan: densely-populated PCB macro with SMD components.
    _IMG.format(pid="photo-1597852074816-d933c7d2b988"),
    # 3  Umberto: blue circuit-board macro with traces and ICs.
    _IMG.format(pid="photo-1555255707-c07966088b7b"),
]

# Explicit per-MPN mapping. Some MPNs share images — better than risking an
# off-topic photo. All four pool entries are verified electronics.
_MPN_IMAGE_INDEX = {
    "OP-27635":         1,  # InP PIC          → yellow fiber strands
    "QSFP-DD-400G-DR4": 1,  # QSFP-DD          → yellow fiber strands
    "AFCT-5765ATZ":     1,  # SFP+ transceiver → yellow fiber strands
    "INPHI-K200Q2-1":   0,  # Coherent DSP     → green PCB w/ chips
    "LX2160ACPE24-RE":  0,  # Network SoC      → green PCB w/ chips
    "GN1103-DQFP":      3,  # PAM4 CDR         → blue circuit board
    "TAS5766MDCA":      3,  # Class-D amp      → blue circuit board
    "CXO7050Q8-106.25": 2,  # VCXO             → dense SMD board
    "VSC8514XKN":       2,  # GbE PHY          → dense SMD board
}


def _part_short_name(description: str) -> str:
    """Pull the short part name out of a verbose datasheet description.

    Strategy: take the text before the first em-dash, en-dash, or comma —
    those almost always separate the part name from spec details.
    Falls back to the first 60 chars if no separator is found.
    """
    if not description:
        return ""
    for sep in (" — ", "—", " – ", "–", ", "):
        if sep in description:
            return description.split(sep, 1)[0].strip()
    return description.strip()[:60]


def image_for_part(part: dict) -> str:
    """Return a distinct image URL for this part.

    Sample-BOM MPNs are explicitly mapped (so each demo part gets a unique
    visual). Unknown MPNs hash deterministically into the pool — same MPN
    always lands on the same image — so non-demo BOMs also get variety.
    """
    mpn = (part.get("mpn") or "").strip()
    if mpn in _MPN_IMAGE_INDEX:
        return _PART_IMAGE_POOL[_MPN_IMAGE_INDEX[mpn]]
    seed = sum(ord(c) for c in mpn) if mpn else 0
    return _PART_IMAGE_POOL[seed % len(_PART_IMAGE_POOL)]


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

        # Expander label — short part name + risk dot + lead/stock only.
        # MPN and price live inside the expanded detail grid, not the row label.
        short_name = _part_short_name(description) or mpn
        icon       = RISK_ICONS[risk]
        label      = (
            f"{icon} &nbsp; **{short_name}**"
            f"&nbsp;&nbsp;&nbsp;&nbsp;{lead_str} lead &nbsp;·&nbsp; {stock_str} stk"
        )

        with st.expander(label):
            # Component image — visual reference for the part type.
            img_url = image_for_part(part)
            st.markdown(
                f'<img class="part-image" src="{img_url}" alt="{mpn}" loading="lazy" />',
                unsafe_allow_html=True,
            )

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
        "Catena — Supply Chain Risk Report",
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


# ─── Hero (scroll-driven word reveal — vanilla port of TextRevealByWord) ────
def render_hero() -> None:
    """
    Word-by-word reveal hero. Words dim → bright as the user scrolls;
    if they don't scroll within ~1s the reveal auto-staggers so the message
    is never stranded as muted gray text. Rendered in components.html so the
    JS can read window.parent.scrollY (same-origin) for true scroll-driven
    opacity, matching the Framer Motion useScroll/useTransform behavior.
    """
    html = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"/>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
  *,*::before,*::after { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; background: transparent;
    font-family: 'Inter', system-ui, -apple-system, sans-serif; color: #0F172A; }

  .hero-wrap {
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    padding: 30px 16px 14px; text-align: center;
  }
  .hero-title {
    display: flex; flex-wrap: wrap; justify-content: center; align-items: baseline;
    max-width: 880px; gap: 0.18em 0.42em; margin: 0 0 14px;
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    font-size: clamp(1.55rem, 3.4vw, 2.5rem);
    font-weight: 800; letter-spacing: -0.025em; line-height: 1.15;
  }
  .hero-word {
    position: relative; display: inline-block;
    color: rgba(15,23,42,0.18);
    transition: color 0.22s ease-out;
    will-change: color;
  }
  .hero-word.lit { color: #0F172A; }
  .hero-word.accent.lit { color: #2563EB; }
  .hero-sub {
    font-size: 0.92rem; font-weight: 500; color: #64748B;
    max-width: 560px; margin: 0; line-height: 1.55; letter-spacing: -0.005em;
    opacity: 0; transform: translateY(6px);
    transition: opacity 0.6s ease-out 0.05s, transform 0.6s ease-out 0.05s;
  }
  .hero-sub.lit { opacity: 1; transform: translateY(0); }
</style>
</head>
<body>
  <div class="hero-wrap">
    <div class="hero-title" id="hero-title"></div>
    <p class="hero-sub" id="hero-sub">Design-Time Supply Chain Intelligence for Photonics OEMs</p>
  </div>
<script>
(function(){
  // "Catena" is index 0 — render it in brand blue when lit.
  var words   = ["Catena", "—", "Supply", "Chain", "Simplified."];
  var accents = { 0: true };
  var title   = document.getElementById("hero-title");
  var sub     = document.getElementById("hero-sub");

  words.forEach(function(w, i) {
    var s = document.createElement("span");
    s.className = "hero-word" + (accents[i] ? " accent" : "");
    s.textContent = w;
    title.appendChild(s);
  });
  var wordEls = title.querySelectorAll(".hero-word");

  // Scroll-driven opacity. Read parent scrollY (same-origin Streamlit page);
  // fall back to own window scrollY if cross-frame access is blocked.
  var SCROLL_END = 360; // px of parent scroll to complete the reveal
  var userScrolled = false;

  function getParentScroll() {
    try { return window.parent.scrollY || window.parent.pageYOffset || 0; }
    catch(e) { return window.scrollY || 0; }
  }

  function tick() {
    var y = getParentScroll();
    if (y > 4) userScrolled = true;
    var p = Math.min(1, Math.max(0, y / SCROLL_END));
    var lit = Math.round(p * words.length);
    wordEls.forEach(function(el, i) {
      el.classList.toggle("lit", i < lit);
    });
    sub.classList.toggle("lit", p > 0.82);
  }

  // Wire parent + self scroll listeners.
  try { window.parent.addEventListener("scroll", tick, { passive: true }); } catch(e) {}
  window.addEventListener("scroll", tick, { passive: true });

  // Initial paint.
  tick();

  // Graceful fallback: if user hasn't scrolled within ~900ms, run the
  // staggered reveal automatically so the hero isn't stuck in muted state.
  setTimeout(function() {
    if (userScrolled) return;
    wordEls.forEach(function(el, i) {
      setTimeout(function(){ el.classList.add("lit"); }, i * 95);
    });
    setTimeout(function(){ sub.classList.add("lit"); }, words.length * 95 + 60);
  }, 900);
})();
</script>
</body>
</html>"""
    components.html(html, height=210, scrolling=False)


# ─── Action buttons (vanilla port of multi-type-ripple-buttons) ─────────────
def render_action_buttons() -> None:
    """Three ripple-effect CTA buttons: Upload BOM, Try Sample BOM, Contact Us.

    Vanilla-JS port of the shadcn RippleButton component. Each button gets a
    click-point ripple animation (circle scales 0→1, fades to 0). Variants:
      - Upload BOM     → hoverborder (animated border on hover)
      - Try Sample BOM → default filled blue (primary action)
      - Contact Us     → hover (background-color fill from cursor)

    "Try Sample BOM" links to ?action=sample which the Python handler reads
    to load SAMPLE_RESULTS. The other two are decorative for the demo.
    """
    html = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"/>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
  *,*::before,*::after { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; background: transparent;
    font-family: 'Inter', system-ui, -apple-system, sans-serif; }

  .btn-row {
    display: flex; justify-content: center; align-items: center;
    gap: 14px; padding: 12px 16px 16px; flex-wrap: wrap;
  }

  /* Shared button skeleton */
  .rb {
    position: relative;
    border: none; background: transparent;
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    font-size: 0.92rem; font-weight: 600; letter-spacing: -0.01em;
    padding: 11px 24px; border-radius: 10px;
    cursor: pointer; overflow: hidden; isolation: isolate;
    transition: transform 0.12s ease, box-shadow 0.18s ease;
    text-decoration: none; display: inline-flex; align-items: center; gap: 8px;
    -webkit-tap-highlight-color: transparent;
  }
  .rb:active { transform: translateY(1px); }
  .rb .rb-label { position: relative; z-index: 2; pointer-events: none; }

  /* Variant: default (primary filled) */
  .rb-default {
    background: #2563EB; color: #FFFFFF;
    box-shadow: 0 1px 3px rgba(37,99,235,0.30), 0 6px 18px rgba(37,99,235,0.20);
  }
  .rb-default:hover { background: #1D4ED8; }

  /* Variant: hoverborder (animated outline ring on hover) */
  .rb-hoverborder {
    color: #0F172A; background: #FFFFFF;
    border: 1px solid rgba(37,99,235,0.18);
  }
  .rb-hoverborder::before {
    content: ''; position: absolute; inset: -1px;
    border-radius: inherit; padding: 1.5px;
    background: conic-gradient(from 0deg, transparent 0deg, #2563EB 90deg,
                               #60A5FA 180deg, #2563EB 270deg, transparent 360deg);
    mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
    -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
    mask-composite: exclude; -webkit-mask-composite: xor;
    opacity: 0; transition: opacity 0.25s ease;
    animation: rb-spin 3s linear infinite;
    z-index: 1; pointer-events: none;
  }
  .rb-hoverborder:hover { color: #2563EB; }
  .rb-hoverborder:hover::before { opacity: 1; }
  @keyframes rb-spin { to { transform: rotate(360deg); } }

  /* Variant: hover (background fills from cursor on hover) */
  .rb-hover {
    color: #0F172A; background: #F1F5F9;
    border: 1px solid rgba(37,99,235,0.10);
  }
  .rb-hover .rb-fill {
    position: absolute; left: 50%; top: 50%;
    width: 0; height: 0; border-radius: 50%;
    background: rgba(105,150,226,0.40);
    transform: translate(-50%, -50%);
    transition: width 0.55s ease, height 0.55s ease;
    z-index: 1; pointer-events: none;
  }
  .rb-hover:hover .rb-fill { width: 380px; height: 380px; }
  .rb-hover:hover { color: #1E40AF; }

  /* Click ripple (all variants) — JS-spawned circles */
  .rb-ripple {
    position: absolute; border-radius: 50%;
    pointer-events: none; z-index: 3;
    transform: scale(0); opacity: 1;
    animation: rb-ripple 600ms ease-out forwards;
  }
  .rb-default .rb-ripple   { background: rgba(255,255,255,0.45); }
  .rb-hoverborder .rb-ripple { background: rgba(37,99,235,0.22); }
  .rb-hover .rb-ripple     { background: rgba(37,99,235,0.20); }
  @keyframes rb-ripple {
    to { transform: scale(1); opacity: 0; }
  }
</style>
</head>
<body>
<div class="btn-row">
  <a class="rb rb-hoverborder" id="rb-upload" href="?action=upload" target="_top">
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor"
         stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
      <polyline points="17 8 12 3 7 8"/>
      <line x1="12" y1="3" x2="12" y2="15"/>
    </svg>
    <span class="rb-label">Upload BOM</span>
  </a>

  <a class="rb rb-default" id="rb-sample" href="?action=sample" target="_top">
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor"
         stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
    </svg>
    <span class="rb-label">Try Sample BOM</span>
  </a>

  <a class="rb rb-hover" id="rb-contact" href="mailto:hello@catena.ai" target="_top">
    <span class="rb-fill"></span>
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor"
         stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round">
      <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
      <polyline points="22,6 12,13 2,6"/>
    </svg>
    <span class="rb-label">Contact Us</span>
  </a>
</div>

<script>
(function() {
  // Click ripple — spawn a circle at the click point on every .rb click.
  document.querySelectorAll('.rb').forEach(function(btn) {
    btn.addEventListener('click', function(e) {
      // Spawn click ripple (visual feedback — unchanged).
      var rect = btn.getBoundingClientRect();
      var size = Math.max(rect.width, rect.height) * 2;
      var x = e.clientX - rect.left - size / 2;
      var y = e.clientY - rect.top  - size / 2;
      var span = document.createElement('span');
      span.className = 'rb-ripple';
      span.style.width = size + 'px';
      span.style.height = size + 'px';
      span.style.left = x + 'px';
      span.style.top  = y + 'px';
      btn.appendChild(span);
      setTimeout(function(){ span.remove(); }, 620);

      // Navigate the parent page. Streamlit's components.html iframe
      // sandbox blocks target="_top" on <a>, so we do it manually.
      // allow-same-origin lets us access window.top.location.
      var href = btn.getAttribute('href');
      if (!href || href === '#') return;
      if (href.indexOf('mailto:') === 0) return;  // mailto: works natively
      e.preventDefault();
      try { window.top.location.href = href; }
      catch (err) {
        try { window.parent.location.href = href; }
        catch (err2) { window.location.href = href; }
      }
    });
  });
})();
</script>
</body>
</html>"""
    components.html(html, height=110, scrolling=False)


# ─── Navbar ──────────────────────────────────────────────────────────────────
def render_navbar() -> None:
    """Top navigation bar — CSS lives in inject_css(), only clean HTML here."""
    logo_url = _logo_data_url()
    # Full Catena composite logo on the right side of the navbar.
    # If the file is missing, fall back to a simple text mark.
    if logo_url:
        logo_html = (
            f'<a class="sl-logo" href="?view=home" target="_self" aria-label="Catena home">'
            f'<img class="sl-logo-img" src="{logo_url}" alt="Catena"/>'
            f'</a>'
        )
    else:
        logo_html = (
            '<a class="sl-logo" href="?view=home" target="_self" '
            'style="font-weight:700;font-size:1.05rem;color:#0F172A;">'
            '&#9889; Catena</a>'
        )

    st.markdown(
        '<div class="sl-nav">'
        '<ul class="sl-menu">'
        '<li class="sl-item"><a class="sl-link" href="?view=home" target="_self">Dashboard</a></li>'
        '<li class="sl-item"><span class="sl-link">Features &#9662;</span>'
        '<div class="sl-drop">'
        '<a class="sl-drop-item" href="#"><div><div class="sl-drop-title">Risk Analysis</div><div class="sl-drop-desc">6-dimension AI risk scoring across your full BOM</div></div></a>'
        '<a class="sl-drop-item" href="#"><div><div class="sl-drop-title">AVL Intelligence</div><div class="sl-drop-desc">Approved Vendor List gap analysis and flow-down checks</div></div></a>'
        '<a class="sl-drop-item" href="#"><div><div class="sl-drop-title">Substitution Engine</div><div class="sl-drop-desc">Design-time alternative part recommendations</div></div></a>'
        '<a class="sl-drop-item" href="#"><div><div class="sl-drop-title">Export Reports</div><div class="sl-drop-desc">Annotated Excel BOM and PDF risk briefings</div></div></a>'
        '</div></li>'
        '<li class="sl-item"><span class="sl-link">Integrations &#9662;</span>'
        '<div class="sl-drop">'
        '<a class="sl-drop-item" href="#"><div><div class="sl-drop-title">ERP Systems</div><div class="sl-drop-desc">SAP, Oracle and NetSuite BOM sync</div></div></a>'
        '<a class="sl-drop-item" href="#"><div><div class="sl-drop-title">Distributor APIs</div><div class="sl-drop-desc">Live pricing from Arrow, Avnet and Digi-Key</div></div></a>'
        '<a class="sl-drop-item" href="#"><div><div class="sl-drop-title">Team Collaboration</div><div class="sl-drop-desc">Share risk reports with procurement and engineering</div></div></a>'
        '</div></li>'
        '<li class="sl-item"><a class="sl-link" href="#">Pricing</a></li>'
        '<li class="sl-item"><a class="sl-link" href="#">Docs</a></li>'
        '</ul>'
        + logo_html +
        '</div>',
        unsafe_allow_html=True,
    )


# ─── Feature section (landing state) ─────────────────────────────────────────
def render_feature_section() -> None:
    """Tabbed feature showcase — light-theme port of Feature108."""
    html = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"/>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
  *, *::before, *::after { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; background: #F4F7FF;
    font-family: 'Inter', system-ui, -apple-system, sans-serif; color: #0F172A; }

  .section  { padding: 32px 0 12px; }
  .container { max-width: 100%; padding: 0 4px; }

  /* Badge */
  .badge {
    display: inline-flex; align-items: center; border-radius: 9999px;
    border: 1px solid rgba(37,99,235,0.22); padding: 3px 13px;
    font-size: 0.68rem; font-weight: 700; color: #2563EB;
    letter-spacing: 0.07em; text-transform: uppercase; background: #EFF6FF;
  }

  /* Header */
  .section-header {
    display: flex; flex-direction: column; align-items: center;
    gap: 14px; text-align: center; margin-bottom: 32px;
  }
  .section-header h1 {
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    font-size: 1.75rem; font-weight: 700; letter-spacing: -0.02em;
    color: #0F172A; max-width: 540px; line-height: 1.25; margin: 0;
  }
  .section-header p { color: #64748B; font-size: 0.875rem; max-width: 460px; line-height: 1.6; margin: 0; }

  /* Tab list */
  .tabs-list { display: flex; justify-content: center; gap: 6px; margin-bottom: 18px; flex-wrap: wrap; }
  .tab-btn {
    display: flex; align-items: center; gap: 7px; padding: 8px 18px;
    border-radius: 10px; border: 1px solid transparent;
    background: transparent; color: #64748B;
    font-size: 0.83rem; font-weight: 600; cursor: pointer;
    transition: all 0.15s; font-family: 'Inter', system-ui, -apple-system, sans-serif; outline: none;
  }
  .tab-btn:hover { background: #F1F5F9; color: #0F172A; border-color: rgba(37,99,235,0.10); }
  .tab-btn.active { background: #EFF6FF; color: #2563EB; border-color: rgba(37,99,235,0.20); }
  .tab-btn svg { width: 15px; height: 15px; flex-shrink: 0; }

  /* Content box */
  .tabs-content {
    background: #FFFFFF; border: 1px solid rgba(37,99,235,0.10);
    border-radius: 18px; padding: 40px;
    box-shadow: 0 4px 16px rgba(15,23,42,0.06);
  }

  /* Panels */
  .tab-panel { display: none; grid-template-columns: 1fr 1fr; gap: 48px; align-items: center; }
  .tab-panel.active { display: grid; animation: panel-in 0.22s ease-out both; }
  @keyframes panel-in { from { opacity:0; transform:translateY(6px); } to { opacity:1; transform:translateY(0); } }

  /* Panel text */
  .panel-text { display: flex; flex-direction: column; gap: 16px; }
  .panel-badge {
    display: inline-flex; align-items: center; border-radius: 9999px;
    border: 1px solid rgba(37,99,235,0.22); padding: 3px 12px;
    font-size: 0.68rem; font-weight: 700; color: #2563EB;
    background: #EFF6FF; letter-spacing: 0.07em; text-transform: uppercase; width: fit-content;
  }
  .panel-title { font-family: 'Inter', system-ui, -apple-system, sans-serif; font-size: 1.6rem; font-weight: 700; letter-spacing: -0.02em; color: #0F172A; line-height: 1.2; margin: 0; }
  .panel-desc  { color: #64748B; line-height: 1.65; font-size: 0.875rem; margin: 0; }
  .panel-btn {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 10px 22px; background: #2563EB; color: #fff;
    border-radius: 9px; border: none; font-size: 0.875rem; font-weight: 600;
    cursor: pointer; width: fit-content; margin-top: 4px;
    font-family: 'Inter', system-ui, -apple-system, sans-serif; transition: background 0.14s;
    box-shadow: 0 1px 4px rgba(37,99,235,0.28);
  }
  .panel-btn:hover { background: #1D4ED8; }
  .panel-img { border-radius: 14px; width: 100%; aspect-ratio: 4/3; object-fit: cover; border: 1px solid rgba(37,99,235,0.10); display: block; box-shadow: 0 4px 20px rgba(15,23,42,0.08); }
</style>
</head>
<body>
<section class="section">
  <div class="container">
    <div class="section-header">
      <span class="badge">Catena</span>
      <h1>Design-time intelligence for every line of your BOM.</h1>
      <p>From photonics PICs to passive components — know your supply chain risk before you're committed to a design.</p>
    </div>

    <div class="tabs-list">
      <button class="tab-btn active" onclick="switchTab(event,'risk')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/></svg>
        Risk Analysis
      </button>
      <button class="tab-btn" onclick="switchTab(event,'avl')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        AVL Intelligence
      </button>
      <button class="tab-btn" onclick="switchTab(event,'sub')">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><line x1="6" y1="3" x2="6" y2="15"/><circle cx="18" cy="6" r="3"/><circle cx="6" cy="18" r="3"/><path d="M18 9a9 9 0 0 1-9 9"/></svg>
        Substitution Engine
      </button>
    </div>

    <div class="tabs-content">
      <div id="panel-risk" class="tab-panel active">
        <div class="panel-text">
          <span class="panel-badge">AI-Powered</span>
          <h3 class="panel-title">Catch 60-week lead times before you're locked in.</h3>
          <p class="panel-desc">Catena analyzes every line of your BOM across six risk dimensions — availability, lead time, cost, lifecycle, geopolitical exposure, and vendor concentration — in seconds. No surprises at procurement.</p>
          <button class="panel-btn">Analyze a BOM &rarr;</button>
        </div>
        <img class="panel-img" src="https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=700&q=80" alt="Risk analytics dashboard" loading="lazy"/>
      </div>
      <div id="panel-avl" class="tab-panel">
        <div class="panel-text">
          <span class="panel-badge">Supplier Aware</span>
          <h3 class="panel-title">Know your AVL gaps before qualification starts.</h3>
          <p class="panel-desc">Catena cross-references your BOM against your Approved Vendor List, surfaces coverage gaps, and flags customer flow-down restrictions — Verizon, AT&T, DoD — that would otherwise surface at contract review.</p>
          <button class="panel-btn">Upload Your AVL &rarr;</button>
        </div>
        <img class="panel-img" src="https://images.unsplash.com/photo-1558494949-ef010cbdcc31?w=700&q=80" alt="Network visualization" loading="lazy"/>
      </div>
      <div id="panel-sub" class="tab-panel">
        <div class="panel-text">
          <span class="panel-badge">Design-Time</span>
          <h3 class="panel-title">Find a drop-in before the shortage hits.</h3>
          <p class="panel-desc">When a part flags RED, Catena surfaces qualified alternatives ranked by compatibility — drop-in, minor rework, or redesign — alongside availability windows and AVL qualification status. Act at design-time, not crunch-time.</p>
          <button class="panel-btn">See Alternatives &rarr;</button>
        </div>
        <img class="panel-img" src="https://images.unsplash.com/photo-1518770660439-4636190af475?w=700&q=80" alt="Electronic components" loading="lazy"/>
      </div>
    </div>
  </div>
</section>
<script>
  function switchTab(event, tabId) {
    document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.tab-panel').forEach(p => { p.classList.remove('active'); p.style.animation='none'; });
    event.currentTarget.classList.add('active');
    var panel = document.getElementById('panel-' + tabId);
    panel.offsetHeight;
    panel.style.animation = '';
    panel.classList.add('active');
  }
</script>
</body></html>"""
    components.html(html, height=660, scrolling=False)


# ─── Testimonials carousel (stacked-card port of TestimonialCarousel) ────────
def render_testimonials() -> None:
    """Customer testimonial carousel — three stacked cards, auto-rotates every
    6 seconds, click arrows or dots to navigate. Vanilla-JS port of the
    Framer Motion shadcn component."""
    html = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"/>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
  *,*::before,*::after { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; background: transparent;
    font-family: 'Inter', system-ui, -apple-system, sans-serif; color: #0F172A; }

  .wrap { padding: 40px 16px 24px; }

  .section-head { text-align: center; max-width: 620px; margin: 0 auto 18px; }
  .badge {
    display: inline-flex; align-items: center; border-radius: 9999px;
    border: 1px solid rgba(37,99,235,0.22); padding: 3px 13px;
    font-size: 0.68rem; font-weight: 700; color: #2563EB;
    letter-spacing: 0.07em; text-transform: uppercase; background: #EFF6FF;
    margin-bottom: 14px;
  }
  .section-title {
    font-family: 'Inter', sans-serif;
    font-size: 1.75rem; font-weight: 800; letter-spacing: -0.025em;
    color: #0F172A; margin: 6px 0 10px; line-height: 1.2;
  }
  .section-sub { color: #64748B; font-size: 0.875rem; margin: 0; line-height: 1.6; }

  .carousel-area {
    position: relative; width: 400px; height: 300px; margin: 36px auto 0;
  }
  .card {
    position: absolute; inset: 0;
    background: #FFFFFF; border: 1px solid rgba(37,99,235,0.10);
    border-radius: 16px;
    box-shadow: 0 12px 32px rgba(15,23,42,0.10), 0 1px 3px rgba(15,23,42,0.05);
    padding: 26px 28px 22px;
    display: flex; flex-direction: column; align-items: center; text-align: center;
    transition: transform 0.5s cubic-bezier(0.4,0,0.2,1),
                opacity 0.5s cubic-bezier(0.4,0,0.2,1);
    transform-origin: 50% 100%;
    will-change: transform, opacity;
  }
  .card-avatar {
    width: 58px; height: 58px; border-radius: 50%;
    border: 2px solid #EFF6FF; object-fit: cover; margin-bottom: 12px;
    box-shadow: 0 1px 4px rgba(15,23,42,0.06);
  }
  .card-quote {
    font-size: 0.875rem; color: #475569; line-height: 1.6; margin: 4px 0 14px;
    font-weight: 500; max-width: 320px;
  }
  .card-name {
    font-size: 0.84rem; font-weight: 700; color: #0F172A; margin: 0 0 2px;
  }
  .card-role {
    font-size: 0.72rem; color: #64748B; font-weight: 500; line-height: 1.4;
  }
  .card-company {
    margin-top: 10px; font-size: 0.7rem; font-weight: 800; color: #2563EB;
    letter-spacing: 0.14em; text-transform: uppercase;
  }

  /* Stacked-card states */
  .card.is-back2 { transform: translateY(22px) scale(0.92) rotate(-3deg);
                   opacity: 0.32; z-index: 1; pointer-events: none; }
  .card.is-back1 { transform: translateY(11px) scale(0.96) rotate(-1.5deg);
                   opacity: 0.6; z-index: 2; pointer-events: none; }
  .card.is-current { transform: translateY(0) scale(1) rotate(0);
                     opacity: 1; z-index: 3; }

  .arrows {
    display: flex; justify-content: space-between; align-items: center;
    width: 400px; margin: 24px auto 0; padding: 0 12px;
  }
  .arrow-btn {
    width: 38px; height: 38px; border-radius: 50%;
    border: 1px solid rgba(37,99,235,0.18); background: #FFFFFF;
    cursor: pointer; color: #2563EB; font-size: 16px; font-weight: 700;
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 1px 3px rgba(15,23,42,0.06);
    transition: all 0.16s;
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
  }
  .arrow-btn:hover { background: #EFF6FF; border-color: #2563EB; transform: translateY(-1px); }
  .arrow-btn:active { transform: translateY(0); }

  .dots-row {
    display: flex; justify-content: center; align-items: center; gap: 7px;
  }
  .dot {
    width: 7px; height: 7px; border-radius: 50%; background: #CBD5E1;
    border: none; cursor: pointer; padding: 0;
    transition: all 0.24s cubic-bezier(0.4,0,0.2,1);
  }
  .dot.active { background: #2563EB; width: 22px; border-radius: 4px; }
  .dot:hover:not(.active) { background: #94A3B8; }
</style>
</head>
<body>
<div class="wrap">
  <div class="section-head">
    <span class="badge">Customer Stories</span>
    <h2 class="section-title">Trusted by photonics OEMs</h2>
    <p class="section-sub">Hardware leaders at Nokia, Cisco, and Ciena ship faster when supply chain risk is solved at design-time, not at procurement.</p>
  </div>

  <div class="carousel-area" id="carousel"></div>

  <div class="arrows">
    <button class="arrow-btn" id="prev" aria-label="Previous testimonial">&larr;</button>
    <div class="dots-row" id="dots"></div>
    <button class="arrow-btn" id="next" aria-label="Next testimonial">&rarr;</button>
  </div>
</div>

<script>
(function() {
  var TESTIMONIALS = [
    {
      name: "Sarah Chen",
      role: "VP, Optical Engineering",
      company: "Nokia",
      avatar: "https://randomuser.me/api/portraits/women/44.jpg",
      quote: "Catena flagged a single-source InP PIC dependency two weeks before tape-out. Three months of redesign avoided \\u2014 the program shipped on schedule."
    },
    {
      name: "Marcus Reyes",
      role: "Director, Component Engineering",
      company: "Cisco",
      avatar: "https://randomuser.me/api/portraits/men/32.jpg",
      quote: "Pulled supply chain reviews from week 30 of the program to week 4. Hardware engineers now ship with full procurement context from day one."
    },
    {
      name: "Priya Patel",
      role: "Senior Director, Supply Chain Strategy",
      company: "Ciena",
      avatar: "https://randomuser.me/api/portraits/women/68.jpg",
      quote: "First tool that actually understands our AVL. It feels like having a senior procurement engineer embedded in every design review."
    }
  ];

  var n = TESTIMONIALS.length;
  var idx = 0;
  var carousel = document.getElementById("carousel");
  var dotsEl = document.getElementById("dots");

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, function(c) {
      return { '&':'&amp;', '<':'&lt;', '>':'&gt;', '"':'&quot;', "'":'&#39;' }[c];
    });
  }

  function makeCard(t) {
    var el = document.createElement("div");
    el.className = "card";
    el.innerHTML = ''
      + '<img class="card-avatar" src="' + t.avatar + '" alt="' + escapeHtml(t.name) + '" />'
      + '<p class="card-quote">“' + escapeHtml(t.quote) + '”</p>'
      + '<h4 class="card-name">' + escapeHtml(t.name) + '</h4>'
      + '<div class="card-role">' + escapeHtml(t.role) + '</div>'
      + '<div class="card-company">' + escapeHtml(t.company) + '</div>';
    return el;
  }

  var cards = TESTIMONIALS.map(makeCard);
  cards.forEach(function(c){ carousel.appendChild(c); });

  var dots = [];
  TESTIMONIALS.forEach(function(_, i) {
    var d = document.createElement("button");
    d.className = "dot";
    d.setAttribute("aria-label", "Go to testimonial " + (i+1));
    d.addEventListener("click", function(){ goTo(i); });
    dotsEl.appendChild(d);
    dots.push(d);
  });

  function render() {
    cards.forEach(function(c, i) {
      c.classList.remove("is-current", "is-back1", "is-back2");
      var pos = ((i - idx) + n) % n;
      if (pos === 0) c.classList.add("is-current");
      else if (pos === 1) c.classList.add("is-back1");
      else c.classList.add("is-back2");
    });
    dots.forEach(function(d, i) {
      d.classList.toggle("active", i === idx);
    });
  }

  function goTo(i) {
    idx = ((i % n) + n) % n;
    render();
    resetTimer();
  }
  function next() { goTo(idx + 1); }
  function prev() { goTo(idx - 1); }

  document.getElementById("next").addEventListener("click", next);
  document.getElementById("prev").addEventListener("click", prev);

  // Pause auto-rotation on hover; resume on leave.
  var carouselArea = document.getElementById("carousel");
  var timer;
  function startTimer() { timer = setInterval(next, 6000); }
  function resetTimer() { clearInterval(timer); startTimer(); }
  carouselArea.addEventListener("mouseenter", function(){ clearInterval(timer); });
  carouselArea.addEventListener("mouseleave", startTimer);

  render();
  startTimer();
})();
</script>
</body>
</html>"""
    components.html(html, height=560, scrolling=False)


# ─── Magnifier hero (port of view-magnifier.tsx) ─────────────────────────────
def _asset_data_url(filename: str, mime: str = "image/jpeg",
                    fallback: str = "") -> str:
    """Read frontend/assets/<filename> if present and return a base64
    data: URL. Falls back to the given URL string if the file is absent."""
    img = Path(__file__).parent / "assets" / filename
    if img.exists():
        b64 = base64.b64encode(img.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{b64}"
    return fallback


def _magnifier_image_url() -> str:
    """Hero magnifier image. Looks for any of the supported filenames in
    frontend/assets/ (Picture1.webp is the user-uploaded data-center shot),
    base64-embeds it, and falls back to a stock fiber-cable photo if none
    are present."""
    candidates = [
        ("Picture1.webp",  "image/webp"),
        ("datacenter.webp", "image/webp"),
        ("datacenter.jpg",  "image/jpeg"),
        ("datacenter.png",  "image/png"),
    ]
    for name, mime in candidates:
        url = _asset_data_url(name, mime=mime, fallback="")
        if url:
            return url
    # Last-resort fallback — canonical Compare Fibre yellow fiber photo.
    return ("https://images.unsplash.com/photo-1558494949-ef010cbdcc31"
            "?auto=format&fit=crop&w=1600&q=80")


def _logo_data_url() -> str:
    """Catena brand logo — base64 data URL. Checks a few likely filenames
    in frontend/assets/ so the user can drop in updated variants without
    having to rename. White-background variants render best on the light
    theme, so newer "logo 2.*" files are preferred over the original."""
    candidates = [
        ("logo 2.jpeg", "image/jpeg"),
        ("logo 2.jpg",  "image/jpeg"),
        ("logo 2.png",  "image/png"),
        ("logo.jpeg",   "image/jpeg"),
        ("logo.jpg",    "image/jpeg"),
        ("logo.png",    "image/png"),
        ("logo.webp",   "image/webp"),
    ]
    for name, mime in candidates:
        url = _asset_data_url(name, mime=mime, fallback="")
        if url:
            return url
    return ""


def render_magnifier() -> None:
    """Press-and-drag-to-zoom hero image. Vanilla-JS port of the Framer
    Motion view-magnifier component: hold the handle on the right edge
    and drag right to zoom in; release to spring back to 1x."""
    src = _magnifier_image_url()
    html = """<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"/>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
  *,*::before,*::after { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; background: transparent; overflow: hidden;
    font-family: 'Inter', system-ui, -apple-system, sans-serif; color: #0F172A; }

  .wrap {
    padding: 48px 24px 56px;
    display: flex; flex-direction: column; align-items: center;
  }
  .section-head { text-align: center; max-width: 640px; margin: 0 auto 26px; }
  .badge {
    display: inline-flex; align-items: center; border-radius: 9999px;
    border: 1px solid rgba(37,99,235,0.22); padding: 3px 13px;
    font-size: 0.68rem; font-weight: 700; color: #2563EB;
    letter-spacing: 0.07em; text-transform: uppercase; background: #EFF6FF;
    margin-bottom: 14px;
  }
  .section-title {
    font-family: 'Inter', sans-serif;
    font-size: 1.75rem; font-weight: 800; letter-spacing: -0.025em;
    color: #0F172A; margin: 6px 0 10px; line-height: 1.2;
  }
  .section-sub {
    color: #64748B; font-size: 0.875rem; margin: 0; line-height: 1.6;
  }
  .hint {
    margin-top: 14px;
    display: inline-flex; align-items: center; gap: 8px;
    font-size: 0.72rem; font-weight: 600; color: #2563EB;
    letter-spacing: 0.06em; text-transform: uppercase;
  }
  .hint-dot {
    width: 6px; height: 6px; border-radius: 50%; background: #2563EB;
    animation: hint-pulse 1.8s ease-in-out infinite;
  }
  @keyframes hint-pulse {
    0%, 100% { opacity: 0.4; transform: scale(1); }
    50%      { opacity: 1;   transform: scale(1.35); }
  }

  .stage {
    position: relative; width: 100%; max-width: 920px;
    margin-top: 12px;
  }
  .frame {
    position: relative; border-radius: 18px;
    transform-origin: center center;
    transition: box-shadow 0.3s ease;
    will-change: transform;
  }
  .frame img {
    width: 100%; display: block; border-radius: 18px;
    border: 1px solid rgba(15,23,42,0.08);
    box-shadow: 0 12px 32px rgba(15,23,42,0.10), 0 1px 3px rgba(15,23,42,0.06);
    user-select: none; -webkit-user-drag: none;
  }
  .frame.zoomed {
    box-shadow: 0 24px 56px rgba(15,23,42,0.20);
  }

  .handle {
    position: absolute;
    right: -18px; top: 50%;
    width: 6px; height: 58px;
    transform: translateY(-50%);
    border-radius: 999px;
    background: #94A3B8; border: none; padding: 0;
    cursor: ew-resize; touch-action: none;
    transition: background 0.18s, height 0.18s, width 0.18s;
  }
  .handle::after {
    content: ''; position: absolute; inset: -12px -10px;
  }
  .handle:hover { background: #64748B; height: 70px; }
  .handle.active {
    background: #2563EB; width: 7px; height: 72px;
    cursor: grabbing;
    box-shadow: 0 0 0 6px rgba(37,99,235,0.12);
  }

  .zoom-readout {
    position: absolute; left: 50%; bottom: -38px;
    transform: translateX(-50%);
    background: #FFFFFF; border: 1px solid rgba(37,99,235,0.18);
    border-radius: 999px; padding: 4px 12px;
    font-size: 0.72rem; font-weight: 700; color: #0F172A;
    letter-spacing: 0.04em;
    opacity: 0; transition: opacity 0.18s;
    box-shadow: 0 4px 12px rgba(15,23,42,0.06);
    pointer-events: none; white-space: nowrap;
  }
  .zoom-readout.visible { opacity: 1; }
  .zoom-readout .accent { color: #2563EB; }
</style>
</head>
<body>
<div class="wrap">
  <div class="section-head">
    <span class="badge">Hyperscale Infrastructure</span>
    <h2 class="section-title">Built for the BOMs that power the internet</h2>
    <p class="section-sub">Catena is designed for the supply chains behind data centers, hyperscalers, and telco networks — where a single missed lead time can stall a $50M program.</p>
    <div class="hint"><span class="hint-dot"></span> Drag the handle to zoom</div>
  </div>

  <div class="stage">
    <div class="frame" id="frame">
      <img id="img" src="__IMG_SRC__" alt="Data center fiber-optic patch panels" draggable="false"/>
      <button class="handle" id="handle" type="button"
              role="slider" aria-label="Drag to zoom"
              aria-valuemin="100" aria-valuemax="160" aria-valuenow="100"></button>
    </div>
    <div class="zoom-readout" id="readout"><span class="accent">100%</span> zoom</div>
  </div>
</div>

<script>
(function(){
  var frame   = document.getElementById('frame');
  var handle  = document.getElementById('handle');
  var readout = document.getElementById('readout');
  var MIN = 1.0, MAX = 1.6;
  var scale = 1, startX = 0, startScale = 1, dragging = false, raf;

  function paint() {
    frame.style.transform = 'scale(' + scale + ')';
    var pct = Math.round(scale * 100);
    handle.setAttribute('aria-valuenow', String(pct));
    readout.firstElementChild.textContent = pct + '%';
  }
  function setScale(s) {
    scale = Math.max(MIN, Math.min(MAX, s));
    paint();
  }
  function springTo(target) {
    cancelAnimationFrame(raf);
    var from = scale, t0 = performance.now(), dur = 360;
    function tick(t) {
      var p = Math.min(1, (t - t0) / dur);
      // ease-out cubic
      var e = 1 - Math.pow(1 - p, 3);
      scale = from + (target - from) * e;
      paint();
      if (p < 1) raf = requestAnimationFrame(tick);
    }
    raf = requestAnimationFrame(tick);
  }

  handle.addEventListener('pointerdown', function(e) {
    dragging = true; startX = e.clientX; startScale = scale;
    handle.classList.add('active');
    frame.classList.add('zoomed');
    readout.classList.add('visible');
    cancelAnimationFrame(raf);
    try { handle.setPointerCapture(e.pointerId); } catch(_) {}
    e.preventDefault();
  });

  handle.addEventListener('pointermove', function(e) {
    if (!dragging) return;
    var dx = e.clientX - startX;
    setScale(startScale + dx * 0.0045);
  });

  function release(e) {
    if (!dragging) return;
    dragging = false;
    handle.classList.remove('active');
    frame.classList.remove('zoomed');
    try { handle.releasePointerCapture(e.pointerId); } catch(_) {}
    springTo(1);
    setTimeout(function(){ readout.classList.remove('visible'); }, 400);
  }
  handle.addEventListener('pointerup',     release);
  handle.addEventListener('pointercancel', release);
  handle.addEventListener('lostpointercapture', release);

  // Keyboard accessibility — arrow keys nudge zoom
  handle.addEventListener('keydown', function(e) {
    if (e.key === 'ArrowRight') { setScale(scale + 0.05); readout.classList.add('visible'); }
    else if (e.key === 'ArrowLeft')  { setScale(scale - 0.05); readout.classList.add('visible'); }
    else return;
    e.preventDefault();
    clearTimeout(handle._kt);
    handle._kt = setTimeout(function(){
      springTo(1);
      setTimeout(function(){ readout.classList.remove('visible'); }, 400);
    }, 900);
  });

  paint();
})();
</script>
</body>
</html>"""
    components.html(html.replace("__IMG_SRC__", src), height=780, scrolling=False)


# ─── Sidebar replaced by top navbar — static defaults ────────────────────────
show_red    = True
show_yellow = True
show_green  = True


# ─── Main ────────────────────────────────────────────────────────────────────
inject_css()
render_navbar()

render_hero()

# ── Action buttons (ripple-styled — Upload / Try Sample / Contact) ───────────
render_action_buttons()

# ── Session state ─────────────────────────────────────────────────────────────
if "results" not in st.session_state:
    st.session_state.results = None

# ── Query-param routing ───────────────────────────────────────────────────────
# Navbar logo + Dashboard link set ?view=home → clear results.
# "Try Sample BOM" ripple button sets ?action=sample → load demo BOM.
view   = st.query_params.get("view")
action = st.query_params.get("action")

if view == "home":
    st.session_state.results = None
    st.query_params.clear()

if action == "sample":
    st.session_state.results = SAMPLE_RESULTS
    st.query_params.clear()

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

    # Download + home row
    col_home, col_dl1, col_dl2, _ = st.columns([1.2, 1.6, 1.6, 3.6])
    with col_home:
        if st.button("← Home", use_container_width=True, key="home_btn"):
            st.session_state.results = None
            st.rerun()
    with col_dl1:
        st.download_button(
            "📊 Annotated BOM (Excel)",
            data=build_excel(results),
            file_name="catena_annotated_bom.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    with col_dl2:
        st.download_button(
            "📄 Risk Report (TXT)",
            data=build_text_report(results),
            file_name="catena_risk_report.txt",
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
    # Landing state — feature showcase + testimonials + magnifier hero
    render_feature_section()
    render_testimonials()
    render_magnifier()
