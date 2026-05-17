import sys
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

sys.path.append(str(Path(__file__).parent.parent))

import streamlit as st
from backend.bom_parser import parse_bom_file
from backend.distributor_api import get_part_data
from backend.risk_engine import score_part, get_risk_summary
from backend.substitution import get_substitutes
from backend.demo_mode import parse_bom_simple, get_mock_substitutes
from backend.report_generator import generate_annotated_bom, generate_pdf_report

st.set_page_config(page_title="ChainSight", page_icon="⚡", layout="wide")

st.markdown("""
<style>
  .block-container { padding-top: 1.5rem; }
  .app-title { font-size: 2.2rem; font-weight: 900; letter-spacing: -1px; }
  .app-sub   { font-size: 1rem; color: #999; margin-top: -8px; margin-bottom: 16px; }
  .risk-badge-RED    { background:#FF4444; color:white; padding:2px 10px; border-radius:12px; font-weight:700; font-size:0.8rem; }
  .risk-badge-YELLOW { background:#FFB800; color:white; padding:2px 10px; border-radius:12px; font-weight:700; font-size:0.8rem; }
  .risk-badge-GREEN  { background:#00C851; color:white; padding:2px 10px; border-radius:12px; font-weight:700; font-size:0.8rem; }
  .dim-label { font-size:0.75rem; color:#888; text-transform:uppercase; letter-spacing:0.5px; }
  .dim-val-RED    { color:#FF4444; font-weight:700; }
  .dim-val-YELLOW { color:#FFB800; font-weight:700; }
  .dim-val-GREEN  { color:#00C851; font-weight:700; }
  .sub-card { background:#f8f9fa; border-left:3px solid #dee2e6; padding:8px 12px; border-radius:4px; margin:4px 0; }
  .sub-drop-in { border-left-color:#00C851; }
  .sub-rework  { border-left-color:#FFB800; }
  .sub-redesign{ border-left-color:#FF4444; }
  hr { margin: 0.5rem 0; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("⚡ ChainSight")
st.caption("Semiconductor Supply Chain Risk Intelligence")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚡ ChainSight")
    st.caption("Semiconductor Supply Chain Risk Intelligence")
    st.markdown("---")
    st.markdown("### Settings")
    show_subs = st.toggle("Show substitutes for flagged parts", value=True)
    st.markdown("---")
    st.markdown("**Risk thresholds**")
    st.caption("Stock RED below")
    stock_red = st.number_input("units", value=50, key="stock_red", label_visibility="collapsed")
    st.caption("Lead time RED above (weeks)")
    lead_red = st.number_input("weeks", value=20, key="lead_red", label_visibility="collapsed")
    st.markdown("---")
    st.markdown("**Sample BOM**")
    sample_path = Path(__file__).parent.parent / "data" / "sample_bom.csv"
    with open(sample_path, "rb") as f:
        st.download_button("⬇ Download sample_bom.csv", f.read(), "sample_bom.csv", "text/csv", use_container_width=True)

# ── Upload ────────────────────────────────────────────────────────────────────
sample_path = Path(__file__).parent.parent / "data" / "sample_bom.csv"

col_up, col_sample = st.columns([3, 1])
uploaded = col_up.file_uploader("Upload Bill of Materials (CSV or Excel)", type=["csv", "xlsx", "xls"], label_visibility="collapsed")
if col_sample.button("⚡ Try sample BOM", use_container_width=True):
    st.session_state["use_sample"] = True

if st.session_state.get("use_sample") and not uploaded:
    with open(sample_path, "rb") as f:
        sample_bytes = f.read()
    st.info("Using built-in sample BOM (10 parts)")
    file_bytes_to_use = sample_bytes
    filename_to_use   = "sample_bom.csv"
    show_buttons      = True
elif uploaded:
    st.success(f"Uploaded: **{uploaded.name}**")
    file_bytes_to_use = None  # read on demand
    filename_to_use   = uploaded.name
    show_buttons      = True
else:
    show_buttons = False

if show_buttons:
    col_a, col_b = st.columns(2)
    run_demo   = col_a.button("🧪 Demo Mode (no API key)", use_container_width=True)
    run_claude = col_b.button("⚡ Analyze with Claude", type="primary", use_container_width=True)

    if run_demo or run_claude:
        st.session_state.pop("parts_analyzed", None)
        st.session_state.pop("use_sample", None)
        file_bytes = file_bytes_to_use if file_bytes_to_use else uploaded.read()

        if run_demo:
            with st.spinner("Parsing BOM…"):
                parts_raw = parse_bom_simple(file_bytes, filename_to_use)
        else:
            with st.spinner("Parsing BOM with Claude…"):
                parts_raw = parse_bom_file(file_bytes, filename_to_use)

        if not parts_raw:
            st.error("Could not parse BOM — check that the file has MPN and Qty columns.")
            st.stop()

        parts_analyzed = []
        bar = st.progress(0, text="Fetching supply chain data…")

        for i, part in enumerate(parts_raw):
            bar.progress((i + 1) / len(parts_raw), text=f"Analyzing {part.get('mpn', '?')}…")
            dist = get_part_data(part.get("mpn", ""))
            risk = score_part(dist)
            enriched = {**part, "distributor_data": dist, "risk": risk, "substitutes": []}

            if show_subs and risk["composite"] in ("RED", "YELLOW"):
                if run_demo:
                    enriched["substitutes"] = get_mock_substitutes(part.get("mpn", ""))
                else:
                    enriched["substitutes"] = get_substitutes(dist, risk["flags"])

            parts_analyzed.append(enriched)

        bar.empty()
        st.session_state["parts_analyzed"] = parts_analyzed
        st.rerun()

# ── Results ───────────────────────────────────────────────────────────────────
EMOJI = {"RED": "🔴", "YELLOW": "🟡", "GREEN": "🟢"}
GRADE_CLASS = {"Drop-in": "sub-drop-in", "Minor rework": "sub-rework", "Redesign required": "sub-redesign"}

if "parts_analyzed" in st.session_state:
    parts = st.session_state["parts_analyzed"]
    summary = get_risk_summary(parts)

    # Summary bar
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Parts", summary["total"])
    c2.metric("🔴 High Risk", summary["RED"])
    c3.metric("🟡 Medium Risk", summary["YELLOW"])
    c4.metric("🟢 Low Risk", summary["GREEN"])

    st.divider()

    # Downloads
    d1, d2 = st.columns(2)
    bom_bytes = generate_annotated_bom(parts)
    pdf_bytes = generate_pdf_report(parts, summary)
    d1.download_button("📥 Annotated BOM (Excel)", bom_bytes, "chainsight_bom.xlsx",
                       "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True)
    d2.download_button("📄 Risk Report (PDF)", pdf_bytes, "chainsight_report.pdf",
                       "application/pdf", use_container_width=True)

    st.divider()

    # Filter
    col_f, _ = st.columns([1, 3])
    risk_filter = col_f.selectbox("Filter by risk level", ["All", "🔴 RED", "🟡 YELLOW", "🟢 GREEN"])
    filter_val = risk_filter.split()[-1] if risk_filter != "All" else "All"

    # Parts table
    for part in parts:
        dist = part.get("distributor_data", {})
        risk = part.get("risk", {})
        flags = risk.get("flags", {})
        composite = risk.get("composite", "GREEN")

        if filter_val != "All" and composite != filter_val:
            continue

        datasheet = dist.get("datasheet_url", "")
        ds_link = f'<a href="{datasheet}" target="_blank">📄 Datasheet</a>' if datasheet else "—"

        label = (
            f'{EMOJI[composite]} **{part.get("mpn")}** &nbsp;'
            f'<span class="risk-badge-{composite}">{composite}</span>'
        )

        with st.expander(f"{EMOJI[composite]}  {part.get('mpn')}  —  {(dist.get('description') or part.get('description') or '')[:70]}"):

            # Core data row
            cols = st.columns([1.5, 1, 1, 1, 1.5, 1])
            cols[0].markdown(f"**Description**\n\n{dist.get('description', '—')}")
            cols[1].metric("Unit Price", f"${dist.get('unit_price', 0):.2f}")
            cols[2].metric("Stock", f"{dist.get('stock', 0):,}")
            cols[3].metric("Lead Time", f"{dist.get('lead_time_weeks', '?')}w")
            cols[4].metric("Provider", dist.get("provider", "—"))
            cols[5].metric("Lifecycle", dist.get("lifecycle_status", "—"))

            r1, r2 = st.columns([3, 1])
            r1.caption(f"Fab: {dist.get('fab_location', '—')}  |  Qty needed: {part.get('quantity', '—')}  |  Ref des: {part.get('reference_designators', '—')}")
            r2.markdown(ds_link, unsafe_allow_html=True)

            st.markdown("**Risk Breakdown**")
            dim_cols = st.columns(5)
            dim_map = [
                ("Availability", flags.get("availability", "—")),
                ("Lead Time",    flags.get("lead_time", "—")),
                ("Cost",         flags.get("cost", "—")),
                ("Lifecycle",    flags.get("lifecycle", "—")),
                ("Geopolitical", flags.get("geopolitical", "—")),
            ]
            for col, (label, val) in zip(dim_cols, dim_map):
                emoji = EMOJI.get(val, "⚪")
                col.markdown(f'<div class="dim-label">{label}</div><div class="dim-val-{val}">{emoji} {val}</div>', unsafe_allow_html=True)

            # Substitutes
            subs = part.get("substitutes", [])
            if subs:
                st.markdown("---")
                st.markdown("**Substitution Options**")
                for sub in subs:
                    grade = sub.get("compatibility_grade", "")
                    css = GRADE_CLASS.get(grade, "")
                    st.markdown(f"""
<div class="sub-card {css}">
<b>{sub.get('mpn')}</b> &nbsp;·&nbsp; {sub.get('manufacturer')} &nbsp;·&nbsp; <b>{grade}</b><br>
<span style="color:#555">{sub.get('key_differences','')}</span><br>
<span style="color:#333">✓ {sub.get('why_better','')}</span><br>
<small style="color:#888">📦 {sub.get('estimated_availability','')}</small>
</div>""", unsafe_allow_html=True)
            elif risk["composite"] in ("RED", "YELLOW") and not show_subs:
                st.caption("Enable 'Show substitutes' in the sidebar to see alternatives.")
