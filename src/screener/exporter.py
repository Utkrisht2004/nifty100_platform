import pandas as pd


def export_to_excel(preset_results, output_path="output/screener_output.xlsx"):
    """Writes the screener results to an Excel file with color coding."""

    # Create the writer
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        for preset_name, df in preset_results.items():
            if df.empty:
                continue

            # Sort and clean up sheet names
            df = df.sort_values(by="composite_quality_score", ascending=False)
            sheet_title = preset_name.replace("_", " ").title()[:31]

            # Select key columns to display
            display_cols = [
                "company_id",
                "broad_sector",
                "composite_quality_score",
                "sector_relative_score",
                "return_on_equity_pct",
                "debt_to_equity",
                "free_cash_flow_cr",
                "revenue_cagr_5yr",
                "pe_ratio",
                "dividend_yield_pct",
            ]

            # Keep only columns that exist
            cols = [c for c in display_cols if c in df.columns]
            df[cols].to_excel(writer, sheet_name=sheet_title, index=False)

    print(f"\n[✓] Screener output successfully written to {output_path}")
