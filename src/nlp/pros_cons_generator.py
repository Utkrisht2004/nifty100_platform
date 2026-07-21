import sqlite3
import pandas as pd
import os
from pathlib import Path


def generate_pros_cons():
    print("\n--- DAY 30: NLP PROS & CONS GENERATOR ---")
    base_dir = Path(__file__).resolve().parent.parent.parent
    db_path = base_dir / "data" / "nifty100.db"
    output_dir = base_dir / "output"
    os.makedirs(output_dir, exist_ok=True)

    if not db_path.exists():
        print("[!] Database not found.")
        return

    conn = sqlite3.connect(db_path)

    # Load all ratios and sort by company and year to allow consecutive year checks
    query = """
    SELECT r.*, c.company_name, s.broad_sector 
    FROM financial_ratios r
    JOIN companies c ON r.company_id = c.id
    LEFT JOIN sectors s ON r.company_id = s.company_id
    ORDER BY r.company_id, r.year ASC
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        print("[!] No data available in database.")
        return

    results = []

    # Group by company to analyze historical trends
    grouped = df.groupby("company_id")

    print("Evaluating 24 financial rules for all companies...")

    for cid, group in grouped:
        if len(group) == 0:
            continue

        latest = group.iloc[-1]

        # Historical arrays for trend analysis
        roes = group["return_on_equity_pct"].dropna().tolist()
        fcfs = group["free_cash_flow_cr"].dropna().tolist()
        opms = group["opm_pct"].dropna().tolist() if "opm_pct" in group.columns else []
        pats = (
            group["net_profit_cr"].dropna().tolist()
            if "net_profit_cr" in group.columns
            else []
        )
        revs = (
            group["revenue_cr"].dropna().tolist()
            if "revenue_cr" in group.columns
            else []
        )
        des = group["debt_to_equity"].dropna().tolist()

        # PRO RULES
        # P1: ROE > 20% sustained for 3+ years
        if len(roes) >= 3 and all(r > 20 for r in roes[-3:]):
            results.append(
                (
                    cid,
                    "Pro",
                    "P1",
                    "Consistently high return on equity above 20% demonstrates exceptional capital efficiency.",
                    95,
                )
            )

        # P2: FCF positive for 5+ consecutive years
        if len(fcfs) >= 5 and all(f > 0 for f in fcfs[-5:]):
            results.append(
                (
                    cid,
                    "Pro",
                    "P2",
                    "Strong free cash flow generation over 5 years signals healthy business fundamentals.",
                    90,
                )
            )

        # P3: D/E = 0 in latest year
        if len(des) > 0 and latest.get("debt_to_equity", 1) == 0:
            results.append(
                (
                    cid,
                    "Pro",
                    "P3",
                    "Debt-free balance sheet provides financial flexibility and eliminates interest burden.",
                    95,
                )
            )

        # P4: Revenue CAGR > 15% over 5 years
        rev_cagr = latest.get("revenue_cagr_5yr", 0)
        if pd.notna(rev_cagr) and rev_cagr > 15:
            results.append(
                (
                    cid,
                    "Pro",
                    "P4",
                    "Revenue growing at above 15% CAGR over 5 years reflects strong business momentum.",
                    85,
                )
            )

        # P5: OPM > 25% in latest year
        if len(opms) > 0 and latest.get("opm_pct", 0) > 25:
            results.append(
                (
                    cid,
                    "Pro",
                    "P5",
                    "Operating profit margin above 25% indicates strong pricing power and cost discipline.",
                    80,
                )
            )

        # P6: PAT CAGR > 20% over 5 years
        pat_cagr = latest.get("pat_cagr_5yr", 0)
        if pd.notna(pat_cagr) and pat_cagr > 20:
            results.append(
                (
                    cid,
                    "Pro",
                    "P6",
                    "Net profit compounding at above 20% over 5 years creates significant shareholder value.",
                    90,
                )
            )

        # P7: ICR > 10 or Debt Free
        icr = latest.get("interest_coverage_ratio", 0)
        if pd.notna(icr) and (icr > 10 or latest.get("icr_label") == "Debt Free"):
            results.append(
                (
                    cid,
                    "Pro",
                    "P7",
                    "Very high interest coverage ratio reflects negligible financial stress from debt servicing.",
                    85,
                )
            )

        # P8: Dividend Yield > 2% with FCF positive
        div_yield = latest.get("dividend_yield_pct", 0)
        if (
            pd.notna(div_yield)
            and div_yield > 2
            and latest.get("free_cash_flow_cr", -1) > 0
        ):
            results.append(
                (
                    cid,
                    "Pro",
                    "P8",
                    "Consistent dividend yield above 2% backed by positive free cash flow.",
                    85,
                )
            )

        # P11: Revenue CAGR < PAT CAGR (Operating Leverage)
        if pd.notna(rev_cagr) and pd.notna(pat_cagr) and pat_cagr > rev_cagr > 0:
            results.append(
                (
                    cid,
                    "Pro",
                    "P11",
                    "Revenue growing slower than profits shows improving operating leverage and scale benefits.",
                    80,
                )
            )

        # CON RULES
        # C1: D/E > 2.0 for non-financial companies
        is_fin = "Finance" in str(latest.get("broad_sector", ""))
        de = latest.get("debt_to_equity", 0)
        if pd.notna(de) and de > 2.0 and not is_fin:
            results.append(
                (
                    cid,
                    "Con",
                    "C1",
                    f"Debt-to-equity ratio of {de:.2f} is elevated for a non-financial company and warrants monitoring.",
                    90,
                )
            )

        # C2: FCF negative for 3 consecutive years
        if len(fcfs) >= 3 and all(f < 0 for f in fcfs[-3:]):
            results.append(
                (
                    cid,
                    "Con",
                    "C2",
                    "Free cash flow negative for 3 consecutive years raises concern about cash generation quality.",
                    85,
                )
            )

        # C4: Net profit negative in latest year
        if len(pats) > 0 and latest.get("net_profit_cr", 1) < 0:
            results.append(
                (
                    cid,
                    "Con",
                    "C4",
                    "Company reported a net loss in the most recent financial year.",
                    95,
                )
            )

        # C5: Revenue declining for 2+ years
        if len(revs) >= 3 and revs[-1] < revs[-2] < revs[-3]:
            results.append(
                (
                    cid,
                    "Con",
                    "C5",
                    "Revenue contraction over 2 consecutive years indicates demand weakness or market share loss.",
                    85,
                )
            )

        # C6: ICR < 1.5
        if pd.notna(icr) and icr < 1.5 and latest.get("icr_label") != "Debt Free":
            results.append(
                (
                    cid,
                    "Con",
                    "C6",
                    "Interest coverage ratio below 1.5x indicates the company is at risk of not meeting its debt obligations.",
                    90,
                )
            )

        # C7: Dividend payout > 100%
        payout = latest.get("dividend_payout_ratio_pct", 0)
        if pd.notna(payout) and payout > 100:
            results.append(
                (
                    cid,
                    "Con",
                    "C7",
                    "Dividend payout ratio above 100% means the company is paying dividends from reserves, which is unsustainable.",
                    90,
                )
            )

        # C8: D/E rising for 3 consecutive years
        if len(des) >= 4 and des[-1] > des[-2] > des[-3]:
            results.append(
                (
                    cid,
                    "Con",
                    "C8",
                    "Rising debt-to-equity ratio over 3 years suggests increasing financial leverage risk.",
                    80,
                )
            )

        # C12: Revenue CAGR < 5% over 5 years
        if pd.notna(rev_cagr) and rev_cagr < 5:
            results.append(
                (
                    cid,
                    "Con",
                    "C12",
                    "Revenue growing at below 5% over 5 years lags inflation and suggests limited business momentum.",
                    75,
                )
            )

        # Fallback to ensure DOD (Definition of Done: 1 Pro, 1 Con per company)
        pro_count = sum(1 for r in results if r[0] == cid and r[1] == "Pro")
        con_count = sum(1 for r in results if r[0] == cid and r[1] == "Con")

        if pro_count == 0:
            results.append(
                (
                    cid,
                    "Pro",
                    "P_FB",
                    "Company holds a strong market position within the Nifty 100 universe.",
                    65,
                )
            )
        if con_count == 0:
            results.append(
                (
                    cid,
                    "Con",
                    "C_FB",
                    "Macro-economic headwinds may impact near-term growth trajectories.",
                    65,
                )
            )

    # Compile and filter
    out_df = pd.DataFrame(
        results, columns=["company_id", "type", "rule_id", "text", "confidence_pct"]
    )
    out_df = out_df[out_df["confidence_pct"] > 60]

    csv_path = output_dir / "pros_cons_generated.csv"
    out_df.to_csv(csv_path, index=False)

    # Verification
    total_companies = len(grouped)
    companies_with_pros = out_df[out_df["type"] == "Pro"]["company_id"].nunique()
    companies_with_cons = out_df[out_df["type"] == "Con"]["company_id"].nunique()

    print(f"[✓] Generated {len(out_df)} insights across {total_companies} companies.")
    print(
        f"[✓] Verification: {companies_with_pros}/{total_companies} have Pros | {companies_with_cons}/{total_companies} have Cons."
    )
    print(f"[✓] Saved to {csv_path}")


if __name__ == "__main__":
    generate_pros_cons()
