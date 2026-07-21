import sqlite3
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from pathlib import Path


def run_profiling():
    print("\n--- DAY 37: CLUSTER PROFILING & STATISTICS (ROBUST EDITION) ---")
    base_dir = Path(__file__).resolve().parent.parent.parent
    db_path = base_dir / "data" / "nifty100.db"
    output_dir = base_dir / "output"
    reports_dir = base_dir / "reports"
    labels_path = output_dir / "cluster_labels.csv"

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
    """
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Isolate latest year per company
    latest_idx = df.groupby("company_id")["year"].idxmax()
    data = df.loc[latest_idx].copy()

    # 1. Cluster Profiling & Naming
    if labels_path.exists():
        labels_df = pd.read_csv(labels_path)
        merged = pd.merge(data, labels_df, on="company_id", how="inner")

        features = [
            "return_on_equity_pct",
            "debt_to_equity",
            "revenue_cagr_5yr",
            "fcf_cagr_5yr",
            "operating_profit_margin_pct",
        ]

        # Inject missing columns with 0.0 to prevent KeyError
        for f in features:
            if f not in merged.columns:
                merged[f] = 0.0

        # Calculate cluster means
        cluster_means = merged.groupby("cluster_id")[features].mean().fillna(0)

        # Dynamic naming heuristic based on ROE
        sorted_clusters = cluster_means.sort_values(
            by="return_on_equity_pct", ascending=False
        ).index.tolist()

        name_mapping = {
            sorted_clusters[0]: "High-Quality Compounders",
            sorted_clusters[1]: "Emerging Growth",
            sorted_clusters[2]: "Defensive Dividend Payers",
            sorted_clusters[3]: "Value Cyclicals",
            sorted_clusters[4]: "Distressed or Turnaround",
        }

        print(
            "[*] Assigning Descriptive Cluster Archetypes based on financial profiles..."
        )
        for cid, name in name_mapping.items():
            print(
                f"    Cluster {cid} -> {name} (Mean ROE: {cluster_means.loc[cid, 'return_on_equity_pct']:.1f}%)"
            )

        labels_df["cluster_name"] = labels_df["cluster_id"].map(name_mapping)
        labels_df.to_csv(labels_path, index=False)
        print(f"[✓] Updated cluster labels saved to {labels_path}")
    else:
        print("[!] cluster_labels.csv not found. Skip naming.")

    # Define 10 Core KPIs for Correlation and Stats
    kpis = [
        "return_on_equity_pct",
        "roce_pct",
        "net_profit_margin_pct",
        "operating_profit_margin_pct",
        "debt_to_equity",
        "asset_turnover",
        "free_cash_flow_cr",
        "revenue_cagr_5yr",
        "pat_cagr_5yr",
        "eps_cagr_5yr",
    ]

    # Ensure columns exist in the main dataset
    for k in kpis:
        if k not in data.columns:
            data[k] = np.nan

    kpi_data = data[kpis].apply(pd.to_numeric, errors="coerce").fillna(0)

    # 2. Correlation Matrix Heatmap
    print("[*] Generating Correlation Heatmap...")
    plt.figure(figsize=(12, 10))
    corr_matrix = kpi_data.corr()
    sns.heatmap(corr_matrix, annot=True, cmap="coolwarm", fmt=".2f", linewidths=0.5)
    plt.title("Pearson Correlation Matrix - Core KPIs (Nifty 100)")

    heatmap_path = reports_dir / "correlation_heatmap.png"
    plt.savefig(heatmap_path, bbox_inches="tight", dpi=300)
    plt.close()
    print(f"[✓] Saved Correlation Heatmap -> {heatmap_path}")

    # 3. Portfolio Statistics (P10 to P90)
    print("[*] Computing Portfolio Statistics...")
    stats_df = kpi_data.describe(percentiles=[0.10, 0.25, 0.50, 0.75, 0.90]).T
    stats_df = stats_df[["mean", "std", "10%", "25%", "50%", "75%", "90%"]].round(2)
    stats_df.index.name = "Metric"

    stats_path = output_dir / "portfolio_stats.csv"
    stats_df.to_csv(stats_path)
    print(f"[✓] Saved Portfolio Stats -> {stats_path}")

    # 4. Outlier Detection (Z-Score > 3 per Sector)
    print("[*] Running Anomaly/Outlier Detection...")
    outliers = []

    data["broad_sector"] = data["broad_sector"].fillna("Unclassified")
    grouped = data.groupby("broad_sector")

    for sector, group in grouped:
        if len(group) < 3:
            continue  # Skip tiny sectors

        for kpi in kpis:
            series = group[kpi].dropna()
            if len(series) < 3 or series.std() == 0:
                continue

            z_scores = (series - series.mean()) / series.std()
            outlier_mask = np.abs(z_scores) > 3

            if outlier_mask.any():
                for idx in series[outlier_mask].index:
                    outliers.append(
                        {
                            "company_id": data.loc[idx, "company_id"],
                            "company_name": data.loc[idx, "company_name"],
                            "sector": sector,
                            "metric": kpi,
                            "value": data.loc[idx, kpi],
                            "z_score": round(z_scores[idx], 2),
                        }
                    )

    outlier_df = pd.DataFrame(outliers)
    outlier_path = output_dir / "outlier_report.csv"
    if not outlier_df.empty:
        outlier_df = outlier_df.sort_values(by="z_score", key=abs, ascending=False)
        outlier_df.to_csv(outlier_path, index=False)
        print(
            f"[!] Flagged {len(outlier_df)} severe statistical outliers -> {outlier_path}"
        )
    else:
        pd.DataFrame(
            columns=[
                "company_id",
                "company_name",
                "sector",
                "metric",
                "value",
                "z_score",
            ]
        ).to_csv(outlier_path, index=False)
        print("[✓] Zero extreme statistical outliers detected across sector bounds.")


if __name__ == "__main__":
    run_profiling()
