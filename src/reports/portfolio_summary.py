import sqlite3
import pandas as pd
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def generate_portfolio_summary():
    print("\n--- DAY 35: PORTFOLIO SUMMARY GENERATION ---")
    base_dir = Path(__file__).resolve().parent.parent.parent
    db_path = base_dir / "data" / "nifty100.db"
    output_dir = base_dir / "reports" / "portfolio"

    if not db_path.exists():
        print("[!] Database not found.")
        return

    conn = sqlite3.connect(db_path)
    import re

    conn.create_function(
        "REGEXP", 2, lambda expr, item: re.compile(expr).search(item) is not None
    )

    query = """
    SELECT r.*, c.company_name, s.broad_sector 
    FROM financial_ratios r
    JOIN companies c ON r.company_id = c.id
    LEFT JOIN sectors s ON r.company_id = s.company_id
    WHERE r.year REGEXP '^[0-9]{4}'
    ORDER BY c.company_name ASC, r.year ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        print("[!] No data found.")
        return

    pdf_path = output_dir / "portfolio_summary.pdf"
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )
    styles = getSampleStyleSheet()
    header_style = ParagraphStyle(
        name="CompHeader",
        fontSize=20,
        textColor=colors.white,
        backColor=colors.black,
        spaceAfter=20,
        alignment=1,
        leftIndent=5,
    )

    kpis = [
        ("ROE (%)", "return_on_equity_pct"),
        ("ROCE (%)", "roce_pct"),
        ("Net Profit Margin (%)", "net_profit_margin_pct"),
        ("Operating Margin (%)", "operating_profit_margin_pct"),
        ("Debt to Equity", "debt_to_equity"),
        ("Asset Turnover", "asset_turnover"),
    ]

    elements = []
    grouped = df.groupby("company_id")

    print(
        f"[*] Processing {len(grouped)} companies for the master portfolio summary..."
    )

    for cid, group in grouped:
        if len(group) < 2:
            continue  # Need at least 2 years for trend arrows

        company_name = group.iloc[-1]["company_name"]
        sector = group.iloc[-1].get("broad_sector", "Unclassified")
        prev = group.iloc[-2]
        curr = group.iloc[-1]

        elements.append(Paragraph(f"<b>{company_name} ({cid})</b>", header_style))
        elements.append(Paragraph(f"<b>Sector:</b> {sector}", styles["Heading3"]))
        elements.append(Spacer(1, 15))

        table_data = [["Metric", "Previous Year", "Latest Year", "Trend"]]

        for label, col in kpis:
            p_val = prev.get(col, 0)
            c_val = curr.get(col, 0)

            p_val = p_val if pd.notna(p_val) else 0
            c_val = c_val if pd.notna(c_val) else 0

            # Trend Logic: 2% flat threshold
            if p_val == 0:
                trend = "(FLAT)"
            else:
                pct_change = (c_val - p_val) / abs(p_val) * 100
                if pct_change > 2.0:
                    trend = "(UP) "
                elif pct_change < -2.0:
                    trend = "(DOWN)"
                else:
                    trend = "(FLAT)"

            table_data.append([label, f"{p_val:.2f}", f"{c_val:.2f}", trend])

        t = Table(table_data, colWidths=[150, 100, 100, 80])
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2c3e50")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("ALIGN", (0, 0), (0, -1), "LEFT"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                    ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.whitesmoke),
                    ("TEXTCOLOR", (3, 1), (3, -1), colors.black),
                    ("FONTNAME", (3, 1), (3, -1), "Helvetica-Bold"),
                ]
            )
        )

        elements.append(t)
        elements.append(PageBreak())

    doc.build(elements)
    print(f"[✓] Generated Master Portfolio Summary PDF -> {pdf_path}")


if __name__ == "__main__":
    generate_portfolio_summary()
