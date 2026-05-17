import io

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

RED = "#FF4444"
YELLOW = "#FFB800"
GREEN = "#00C851"
DARK = "#1a1a2e"

RISK_COLS = ["Overall Risk", "Availability", "Lead Time", "Cost", "Lifecycle", "Geo Risk"]
FLAG_KEYS = ["composite", "availability", "lead_time", "cost", "lifecycle", "geopolitical"]


def _risk_color(val: str):
    return {"RED": RED, "YELLOW": YELLOW, "GREEN": GREEN}.get(val)


def generate_annotated_bom(parts: list[dict]) -> bytes:
    rows = []
    for p in parts:
        dist = p.get("distributor_data", {})
        risk = p.get("risk", {})
        flags = risk.get("flags", {})
        rows.append({
            "MPN": p.get("mpn", ""),
            "Manufacturer": p.get("manufacturer", ""),
            "Qty": p.get("quantity", ""),
            "Ref Des": p.get("reference_designators", ""),
            "Description": dist.get("description", p.get("description", "")),
            "Provider": dist.get("provider", ""),
            "Unit Price ($)": dist.get("unit_price", ""),
            "Stock": dist.get("stock", ""),
            "Lead Time (wks)": dist.get("lead_time_weeks", ""),
            "Lifecycle": dist.get("lifecycle_status", ""),
            "Fab Location": dist.get("fab_location", ""),
            "Datasheet": dist.get("datasheet_url", ""),
            "Overall Risk": risk.get("composite", ""),
            "Availability": flags.get("availability", ""),
            "Lead Time": flags.get("lead_time", ""),
            "Cost": flags.get("cost", ""),
            "Lifecycle": flags.get("lifecycle", ""),
            "Geo Risk": flags.get("geopolitical", ""),
        })

    df = pd.DataFrame(rows)
    out = io.BytesIO()

    with pd.ExcelWriter(out, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name="BOM Analysis", index=False)
        wb = writer.book
        ws = writer.sheets["BOM Analysis"]

        red_fmt = wb.add_format({"bg_color": RED, "font_color": "white", "bold": True, "align": "center"})
        yel_fmt = wb.add_format({"bg_color": YELLOW, "font_color": "white", "bold": True, "align": "center"})
        grn_fmt = wb.add_format({"bg_color": GREEN, "font_color": "white", "bold": True, "align": "center"})
        fmt_map = {"RED": red_fmt, "YELLOW": yel_fmt, "GREEN": grn_fmt}

        for col_name in RISK_COLS:
            if col_name not in df.columns:
                continue
            col_idx = df.columns.get_loc(col_name)
            for row_idx, val in enumerate(df[col_name], start=1):
                fmt = fmt_map.get(val)
                if fmt:
                    ws.write(row_idx, col_idx, val, fmt)

        for i, col in enumerate(df.columns):
            ws.set_column(i, i, max(16, len(str(col)) + 4))

    out.seek(0)
    return out.read()


def generate_pdf_report(parts: list[dict], summary: dict) -> bytes:
    out = io.BytesIO()
    doc = SimpleDocTemplate(
        out,
        pagesize=landscape(letter),
        rightMargin=0.5 * inch,
        leftMargin=0.5 * inch,
        topMargin=0.5 * inch,
        bottomMargin=0.5 * inch,
    )
    styles = getSampleStyleSheet()
    h1 = ParagraphStyle("h1", parent=styles["Heading1"], fontSize=20, spaceAfter=4)
    sub = ParagraphStyle("sub", parent=styles["Normal"], fontSize=10, textColor=colors.HexColor("#666666"), spaceAfter=12)
    body = styles["Normal"]
    body.fontSize = 8

    elems = []
    elems.append(Paragraph("ChainSight — Supply Chain Risk Report", h1))
    elems.append(Paragraph(
        f"Total: {summary['total']}  |  🔴 High Risk: {summary['RED']}  |  🟡 Medium: {summary['YELLOW']}  |  🟢 Low: {summary['GREEN']}",
        sub,
    ))

    headers = ["MPN", "Mfr", "Qty", "Description", "Provider", "Price", "Stock", "Lead\nTime", "Lifecycle", "Risk"]
    table_data = [headers]

    for p in parts:
        dist = p.get("distributor_data", {})
        risk = p.get("risk", {})
        desc = (dist.get("description") or p.get("description") or "")[:45]
        table_data.append([
            p.get("mpn", ""),
            (p.get("manufacturer") or "")[:14],
            str(p.get("quantity", "")),
            desc,
            dist.get("provider", ""),
            f"${dist.get('unit_price', 0):.2f}",
            f"{dist.get('stock', 0):,}",
            f"{dist.get('lead_time_weeks', '?')}w",
            dist.get("lifecycle_status", ""),
            risk.get("composite", ""),
        ])

    tbl = Table(table_data, repeatRows=1, hAlign="LEFT")
    style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(DARK)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 7),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("ALIGN", (3, 1), (3, -1), "LEFT"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f5f5")]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#cccccc")),
        ("PADDING", (0, 0), (-1, -1), 4),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ])

    risk_col = len(headers) - 1
    for row_idx, p in enumerate(parts, 1):
        c = p.get("risk", {}).get("composite", "")
        color = _risk_color(c)
        if color:
            style.add("BACKGROUND", (risk_col, row_idx), (risk_col, row_idx), colors.HexColor(color))
            style.add("TEXTCOLOR", (risk_col, row_idx), (risk_col, row_idx), colors.white)
            style.add("FONTNAME", (risk_col, row_idx), (risk_col, row_idx), "Helvetica-Bold")

    tbl.setStyle(style)
    elems.append(tbl)

    flagged = [p for p in parts if p.get("risk", {}).get("composite") in ("RED", "YELLOW")]
    if flagged:
        elems.append(Spacer(1, 0.25 * inch))
        elems.append(Paragraph("Flagged Parts — Substitution Recommendations", styles["Heading2"]))
        for p in flagged:
            elems.append(Spacer(1, 0.08 * inch))
            c = p.get("risk", {}).get("composite", "")
            color = RED if c == "RED" else YELLOW
            elems.append(Paragraph(
                f'<font color="{color}"><b>● {p.get("mpn")} [{c}]</b></font> — {p.get("distributor_data", {}).get("description", "")[:60]}',
                styles["Normal"],
            ))
            for sub in p.get("substitutes", [])[:3]:
                grade = sub.get("compatibility_grade", "")
                g_color = GREEN if grade == "Drop-in" else (YELLOW if grade == "Minor rework" else RED)
                elems.append(Paragraph(
                    f'&nbsp;&nbsp;→ <b>{sub.get("mpn")}</b> ({sub.get("manufacturer")}) '
                    f'<font color="{g_color}">[{grade}]</font>: {sub.get("why_better", "")}',
                    styles["Normal"],
                ))

    doc.build(elems)
    out.seek(0)
    return out.read()
