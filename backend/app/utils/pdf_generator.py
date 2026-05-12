"""
Monthly PDF report generator using ReportLab.
"""
import io
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table,
    TableStyle, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT


def generate_monthly_report(
    month_str: str,          # "2024-03"
    transactions: list[dict],
    income_list: list[dict],
    summary: dict,
) -> bytes:
    """Generate a PDF report and return as bytes."""

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40, leftMargin=40,
        topMargin=40, bottomMargin=40,
    )

    styles = getSampleStyleSheet()

    # ── Custom styles ──────────────────────────────────────
    title_style = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontSize=24,
        textColor=colors.HexColor("#1a1a2e"),
        spaceAfter=6,
        alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=colors.HexColor("#666666"),
        spaceAfter=20,
        alignment=TA_CENTER,
    )
    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=colors.HexColor("#16213e"),
        spaceBefore=16,
        spaceAfter=8,
        borderPad=4,
    )
    normal = styles["Normal"]

    # ── Parse month ────────────────────────────────────────
    try:
        month_dt = datetime.strptime(month_str, "%Y-%m")
        month_label = month_dt.strftime("%B %Y")
    except Exception:
        month_label = month_str

    # ── Filter data for this month ─────────────────────────
    def in_month(date_str):
        if not date_str:
            return False
        return str(date_str)[:7] == month_str

    month_txs = [t for t in transactions if in_month(t.get("date"))]
    month_income = [i for i in income_list if in_month(i.get("date"))]

    total_spent  = sum(t["amount"] for t in month_txs)
    total_income = sum(i["amount"] for i in month_income)
    total_savings = total_income - total_spent
    savings_rate = round((total_savings / total_income * 100), 1) if total_income > 0 else 0

    # ── Category breakdown ─────────────────────────────────
    cat_totals: dict = {}
    for t in month_txs:
        cat = t.get("category", "uncategorized")
        cat_totals[cat] = cat_totals.get(cat, 0) + t["amount"]

    # ── Anomalies ──────────────────────────────────────────
    anomalies = [t for t in month_txs if t.get("is_anomaly")]

    # ── Top 5 expenses ─────────────────────────────────────
    top5 = sorted(month_txs, key=lambda x: x["amount"], reverse=True)[:5]

    # ── Build PDF elements ─────────────────────────────────
    elements = []

    # Header
    elements.append(Paragraph("💰 Finance Report", title_style))
    elements.append(Paragraph(month_label, subtitle_style))
    elements.append(Paragraph(
        f"Generated on {datetime.now().strftime('%d %b %Y at %I:%M %p')}",
        subtitle_style
    ))
    elements.append(HRFlowable(width="100%", thickness=2,
                               color=colors.HexColor("#4ECDC4")))
    elements.append(Spacer(1, 12))

    # ── Summary table ──────────────────────────────────────
    elements.append(Paragraph("📊 Monthly Summary", section_style))

    summary_data = [
        ["Metric", "Amount"],
        ["💵 Total Income",  f"₹{total_income:,.2f}"],
        ["💸 Total Spent",   f"₹{total_spent:,.2f}"],
        ["🏦 Total Saved",   f"₹{total_savings:,.2f}"],
        ["📈 Savings Rate",  f"{savings_rate}%"],
        ["📋 Transactions",  str(len(month_txs))],
        ["🚨 Anomalies",     str(len(anomalies))],
    ]
    summary_table = Table(summary_data, colWidths=[3*inch, 3*inch])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), colors.HexColor("#16213e")),
        ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, 0), 12),
        ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#f8f9fa"), colors.white]),
        ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
        ("TOPPADDING",   (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 8),
        # Highlight savings row
        ("TEXTCOLOR",    (1, 3), (1, 3),
         colors.HexColor("#28a745") if total_savings >= 0
         else colors.HexColor("#dc3545")),
        ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 16))

    # ── Category breakdown ─────────────────────────────────
    if cat_totals:
        elements.append(Paragraph("📂 Spending by Category", section_style))
        cat_data = [["Category", "Amount", "% of Total"]]
        for cat, amt in sorted(cat_totals.items(),
                               key=lambda x: x[1], reverse=True):
            pct = round((amt / total_spent * 100), 1) if total_spent > 0 else 0
            cat_data.append([
                cat.title(),
                f"₹{amt:,.2f}",
                f"{pct}%",
            ])
        cat_table = Table(cat_data, colWidths=[2.5*inch, 2*inch, 1.5*inch])
        cat_table.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, 0), colors.HexColor("#4ECDC4")),
            ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
            ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN",        (1, 0), (-1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.HexColor("#f8f9fa"), colors.white]),
            ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
            ("TOPPADDING",   (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 7),
            ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
        ]))
        elements.append(cat_table)
        elements.append(Spacer(1, 16))

    # ── Top 5 expenses ─────────────────────────────────────
    if top5:
        elements.append(Paragraph("🔥 Top 5 Biggest Expenses", section_style))
        top5_data = [["#", "Description", "Category", "Amount", "Date"]]
        for i, t in enumerate(top5, 1):
            top5_data.append([
                str(i),
                t["description"][:30],
                t.get("category", "—").title(),
                f"₹{t['amount']:,.2f}",
                str(t.get("date", ""))[:10],
            ])
        top5_table = Table(top5_data,
                           colWidths=[0.4*inch, 2.2*inch, 1.4*inch,
                                      1.2*inch, 1.0*inch])
        top5_table.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, 0), colors.HexColor("#FF6B6B")),
            ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
            ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.HexColor("#fff5f5"), colors.white]),
            ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
            ("TOPPADDING",   (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 7),
            ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
        ]))
        elements.append(top5_table)
        elements.append(Spacer(1, 16))

    # ── Anomaly alerts ─────────────────────────────────────
    if anomalies:
        elements.append(Paragraph("🚨 Anomaly Alerts", section_style))
        anomaly_data = [["Description", "Amount", "Date", "Score"]]
        for a in anomalies:
            anomaly_data.append([
                a["description"][:30],
                f"₹{a['amount']:,.2f}",
                str(a.get("date", ""))[:10],
                str(round(a.get("anomaly_score", 0), 3)),
            ])
        anomaly_table = Table(anomaly_data,
                              colWidths=[2.5*inch, 1.5*inch, 1.2*inch, 1.0*inch])
        anomaly_table.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, 0), colors.HexColor("#dc3545")),
            ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
            ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.HexColor("#fff0f0"), colors.white]),
            ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
            ("TOPPADDING",   (0, 0), (-1, -1), 7),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 7),
            ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
        ]))
        elements.append(anomaly_table)
        elements.append(Spacer(1, 16))

    # ── All transactions ───────────────────────────────────
    if month_txs:
        elements.append(Paragraph("📋 All Transactions", section_style))
        tx_data = [["Date", "Description", "Category", "Amount"]]
        for t in sorted(month_txs,
                        key=lambda x: str(x.get("date", "")),
                        reverse=True):
            tx_data.append([
                str(t.get("date", ""))[:10],
                t["description"][:28],
                t.get("category", "—").title(),
                f"₹{t['amount']:,.2f}",
            ])
        tx_table = Table(tx_data,
                         colWidths=[1.2*inch, 2.5*inch, 1.5*inch, 1.0*inch])
        tx_table.setStyle(TableStyle([
            ("BACKGROUND",   (0, 0), (-1, 0), colors.HexColor("#16213e")),
            ("TEXTCOLOR",    (0, 0), (-1, 0), colors.white),
            ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
            ("ALIGN",        (0, 0), (-1, -1), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.HexColor("#f8f9fa"), colors.white]),
            ("GRID",         (0, 0), (-1, -1), 0.5, colors.HexColor("#dee2e6")),
            ("TOPPADDING",   (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 6),
            ("FONTNAME",     (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE",     (0, 1), (-1, -1), 9),
        ]))
        elements.append(tx_table)

    # ── Footer ─────────────────────────────────────────────
    elements.append(Spacer(1, 20))
    elements.append(HRFlowable(width="100%", thickness=1,
                               color=colors.HexColor("#dee2e6")))
    elements.append(Paragraph(
        "Generated by AI Finance Analyzer · For personal use only",
        subtitle_style
    ))

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()