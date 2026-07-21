import sqlite3
import pandas as pd
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle


def generate_sector_reports():
    print("\n--- DAY 34: SECTOR BATCH GENERATION ---")
    base_dir = Path(__file__).resolve().parent.parent.parent
    db_path = base_dir / "data" / "nifty100.db"
    output_dir = base_dir / "reports" / "sector"

    if not db_path.exists():
        print("[!] Database not found.")
        return

    conn = sqlite3.connect(db_path)
    query = """
    SELECT r.*, c.company_name, s.broad_sector 
    FROM financial_ratios r
    JOIN companies c ON r.company_id = c.id
    LEFT JOIN sectors s ON r.company_id = s.company_id
    WHERE r.year REGEXP '^[0-9]{4}'
    """
    # Monkey-patch SQLite for REGEXP
    import re

    conn.create_function(
        "REGEXP", 2, lambda expr, item: re.compile(expr).search(item) is not None
    )

    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        print("[!] No data found.")
        return

    # Isolate latest year per company
    latest_idx = df.groupby("company_id")["year"].idxmax()
    latest_df = df.loc[latest_idx].copy()

    # Fill missing sectors so we don't drop them
    latest_df["broad_sector"] = latest_df["broad_sector"].fillna("Unclassified")

    sectors = latest_df["broad_sector"].unique()
    print(f"[*] Found {len(sectors)} sectors. Generating reports...")

    styles = getSampleStyleSheet()
    header_style = ParagraphStyle(
        name="Header",
        fontSize=18,
        textColor=colors.whitesmoke,
        backColor=colors.darkblue,
        spaceAfter=15,
        alignment=1,
        leftIndent=5,
    )

    metrics = [
        ("ROE %", "return_on_equity_pct"),
        ("ROCE %", "roce_pct"),
        ("Net Margin %", "net_profit_margin_pct"),
        ("Op Margin %", "operating_profit_margin_pct"),
        ("Debt/Equity", "debt_to_equity"),
        ("Asset Turn", "asset_turnover"),
        ("FCF (Cr)", "free_cash_flow_cr"),
        ("PAT CAGR 5Y", "pat_cagr_5yr"),
    ]

    success_count = 0
    for sector in sectors:
        sector_data = latest_df[latest_df["broad_sector"] == sector].copy()

        # Calculate Sector Medians
        medians = sector_data[[m[1] for m in metrics]].median().to_dict()

        pdf_path = (
            output_dir / f"{str(sector).replace('/', '_').replace(' ', '_')}_report.pdf"
        )
        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=landscape(A4),
            rightMargin=20,
            leftMargin=20,
            topMargin=20,
            bottomMargin=20,
        )

        elements = []
        elements.append(Paragraph(f"<b>Sector Summary: {sector}</b>", header_style))
        elements.append(Spacer(1, 10))

        # Build Table Data
        table_data = [["Company"] + [m[0] for m in metrics]]

        # Add Median Row
        median_row = ["SECTOR MEDIAN"] + [
            f"{medians[m[1]]:.2f}" if pd.notna(medians[m[1]]) else "N/A"
            for m in metrics
        ]
        table_data.append(median_row)

        # Add Company Rows
        for _, row in sector_data.sort_values("company_name").iterrows():
            comp_row = [row["company_name"][:20]]  # Truncate long names
            for _, col_name in metrics:
                val = row.get(col_name)
                comp_row.append(
                    f"{val:.2f}"
                    if pd.notna(val) and isinstance(val, (int, float))
                    else "N/A"
                )
            table_data.append(comp_row)

        t = Table(table_data, colWidths=[120] + [80] * 8)
        t.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.darkslategray),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("BACKGROUND", (0, 1), (-1, 1), colors.lightgrey),
                    ("FONTNAME", (0, 1), (-1, 1), "Helvetica-Bold"),
                    ("GRID", (0, 0), (-1, -1), 1, colors.silver),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )

        elements.append(t)
        doc.build(elements)
        success_count += 1

    print(f"[✓] Generated {success_count} Sector PDFs in reports/sector/")


if __name__ == "__main__":
    generate_sector_reports()
