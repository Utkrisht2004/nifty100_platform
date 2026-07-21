import pandas as pd
import re
import os
import sqlite3
from pathlib import Path


def run_parser():
    print("\n--- DAY 29: NLP ANALYSIS PARSER (DYNAMIC HEADER EDITION) ---")
    base_dir = Path(__file__).resolve().parent.parent.parent
    output_dir = base_dir / "output"
    os.makedirs(output_dir, exist_ok=True)

    analysis_path = base_dir / "data" / "raw" / "analysis.xlsx"
    db_path = base_dir / "data" / "nifty100.db"

    if not analysis_path.exists():
        print(f"[!] Warning: {analysis_path} not found.")
        return

    try:
        # Read raw without headers to hunt for the real ones
        raw_df = pd.read_excel(analysis_path, header=None)

        # Scan the first 10 rows to find where the actual headers start
        header_row_idx = 0
        for idx, row in raw_df.head(10).iterrows():
            row_text = " ".join(str(val).lower() for val in row.values)
            if "company" in row_text or "sales" in row_text or "growth" in row_text:
                header_row_idx = idx
                break

        # Reload the dataframe using the correct row as the header
        df = pd.read_excel(analysis_path, skiprows=header_row_idx)
        print(
            f"[*] Successfully loaded analysis.xlsx (Skipped {header_row_idx} title rows)."
        )
        print(f"[*] Actual Columns Found: {df.columns.tolist()}")
    except Exception as e:
        print(f"[!] Failed to read analysis.xlsx: {e}")
        return

    # Normalize column names to make matching bulletproof
    df.columns = df.columns.astype(str).str.strip().str.lower().str.replace(" ", "_")

    # We will look for anything containing these core financial keywords
    target_keywords = ["sales", "profit", "cagr", "roe", "return_on_equity", "growth"]

    # Identify which normalized columns match our targets
    matched_cols = []
    for col in df.columns:
        if any(keyword in col for keyword in target_keywords):
            matched_cols.append(col)

    print(f"[*] Targeting these normalized columns: {matched_cols}")

    # Screener format usually looks like: "10 Years: 15%" or "5Years 12%"
    # This regex is highly forgiving of spacing, colons, and negative numbers
    pattern = re.compile(r"(\d+)\s*[Yy]ears?[^\d-]*(-?[\d.]+)%?")

    parsed_records = []
    failed_records = []

    print("Parsing text fields...")
    for index, row in df.iterrows():
        # Dynamically find the company ID column
        cid_col = next(
            (c for c in df.columns if "company" in c or "id" in c or "ticker" in c),
            None,
        )
        company_id = (
            row[cid_col] if cid_col and pd.notna(row[cid_col]) else f"UNKNOWN_{index}"
        )

        for field in matched_cols:
            if pd.notna(row[field]):
                text_content = str(row[field])
                matches = pattern.findall(text_content)

                if matches:
                    for period, val in matches:
                        parsed_records.append(
                            {
                                "company_id": company_id,
                                "metric_type": field,
                                "period_years": int(period),
                                "value_pct": float(val),
                            }
                        )
                else:
                    # Only log failures if there's actually text that looks like it should contain a number
                    if any(char.isdigit() for char in text_content):
                        failed_records.append(
                            {
                                "company_id": company_id,
                                "metric_type": field,
                                "raw_text": text_content,
                            }
                        )

    parsed_df = pd.DataFrame(parsed_records)
    failures_df = pd.DataFrame(failed_records)

    if not parsed_df.empty:
        parsed_csv_path = output_dir / "analysis_parsed.csv"
        parsed_df.to_csv(parsed_csv_path, index=False)
        print(f"[✓] Extracted {len(parsed_df)} metrics to {parsed_csv_path}")
    else:
        print(
            "[!] Still extracted 0 metrics. The text format in the Excel cells might not contain 'X Years: Y%' patterns."
        )

    if not failures_df.empty:
        failures_csv_path = output_dir / "parse_failures.csv"
        failures_df.to_csv(failures_csv_path, index=False)
        print(
            f"[✓] Logged {len(failures_df)} unparseable entries to {failures_csv_path}"
        )

    # --- CROSS-VALIDATION ENGINE ---
    print("\nExecuting cross-validation against Ratio Engine...")
    if not parsed_df.empty and db_path.exists():
        conn = sqlite3.connect(db_path)
        ratios_query = """
        SELECT company_id, revenue_cagr_5yr, pat_cagr_5yr, return_on_equity_pct
        FROM financial_ratios 
        WHERE year = (SELECT MAX(year) FROM financial_ratios r2 WHERE r2.company_id = financial_ratios.company_id)
        """
        try:
            ratios_df = pd.read_sql_query(ratios_query, conn)
        except Exception as e:
            print(f"[!] Could not query ratio engine: {e}")
            ratios_df = pd.DataFrame()
        conn.close()

        if not ratios_df.empty:
            five_yr_data = parsed_df[parsed_df["period_years"] == 5].copy()
            validation_flags = []

            for _, parsed_row in five_yr_data.iterrows():
                cid = parsed_row["company_id"]
                metric = parsed_row["metric_type"]
                parsed_val = parsed_row["value_pct"]

                db_match = ratios_df[ratios_df["company_id"] == cid]
                if db_match.empty:
                    continue

                db_val = None
                if "sales" in metric or "revenue" in metric:
                    db_val = db_match.iloc[0]["revenue_cagr_5yr"]
                elif "profit" in metric or "pat" in metric:
                    db_val = db_match.iloc[0]["pat_cagr_5yr"]

                if db_val is not None and pd.notna(db_val):
                    diff = abs(parsed_val - db_val)
                    if diff > 5.0:  # Flag if divergence is greater than 5%
                        validation_flags.append(
                            {
                                "company_id": cid,
                                "metric": metric,
                                "parsed_value": parsed_val,
                                "db_value": db_val,
                                "divergence": diff,
                            }
                        )

            if validation_flags:
                flags_df = pd.DataFrame(validation_flags)
                flags_path = output_dir / "cagr_divergence_flags.csv"
                flags_df.to_csv(flags_path, index=False)
                print(
                    f"[!] Flagged {len(flags_df)} anomalies with >5% divergence. Saved to {flags_path}"
                )
            else:
                print("[✓] Cross-validation complete. No severe divergences detected.")
        else:
            print("[!] Ratio Engine data unavailable for validation.")


if __name__ == "__main__":
    run_parser()
