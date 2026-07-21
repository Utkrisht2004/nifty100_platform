import sqlite3
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import os
from pathlib import Path


def run_clustering():
    print("\n--- DAY 36: KMEANS CLUSTERING ENGINE ---")
    base_dir = Path(__file__).resolve().parent.parent.parent
    db_path = base_dir / "data" / "nifty100.db"
    output_dir = base_dir / "output"
    reports_dir = base_dir / "reports"
    os.makedirs(output_dir, exist_ok=True)
    os.makedirs(reports_dir, exist_ok=True)

    if not db_path.exists():
        print("[!] Database not found.")
        return

    conn = sqlite3.connect(db_path)
    # Patch SQLite for REGEXP
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

    # Isolate latest year per company for clustering
    latest_idx = df.groupby("company_id")["year"].idxmax()
    data = df.loc[latest_idx].copy()

    # Define target features
    features = [
        "return_on_equity_pct",
        "debt_to_equity",
        "revenue_cagr_5yr",
        "fcf_cagr_5yr",
        "operating_profit_margin_pct",
    ]

    # Ensure all feature columns exist, inject NaNs if missing so imputation handles them
    for f in features:
        if f not in data.columns:
            data[f] = np.nan

    # 1. Impute missing values with Sector Median
    data["broad_sector"] = data["broad_sector"].fillna("Unclassified")

    print("[*] Imputing missing values with sector medians...")
    for feature in features:
        # Fill with sector median first
        data[feature] = data.groupby("broad_sector")[feature].transform(
            lambda x: x.fillna(x.median())
        )
        # Fallback to global median if a whole sector is NaN
        global_median = data[feature].median()
        data[feature] = data[feature].fillna(
            global_median if pd.notna(global_median) else 0.0
        )

    # Extract feature matrix
    X_raw = data[features].values

    # 2. Scale Features (Zero Mean, Unit Variance)
    print("[*] Normalizing features (StandardScaler)...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_raw)

    # 3. Generate Elbow Plot (k=2 to 10)
    print("[*] Generating Elbow Plot...")
    inertias = []
    k_range = range(2, 11)

    for k in k_range:
        kmeans_temp = KMeans(n_clusters=k, random_state=42, n_init=10)
        kmeans_temp.fit(X_scaled)
        inertias.append(kmeans_temp.inertia_)

    plt.figure(figsize=(8, 5))
    plt.plot(k_range, inertias, marker="o", linestyle="--", color="b")
    plt.title("KMeans Clustering - Elbow Method")
    plt.xlabel("Number of Clusters (k)")
    plt.ylabel("Inertia (WCSS)")
    plt.grid(True, linestyle=":", alpha=0.7)

    elbow_path = reports_dir / "elbow_plot.png"
    plt.savefig(elbow_path, bbox_inches="tight", dpi=300)
    plt.close()
    print(f"[✓] Saved Elbow Plot -> {elbow_path}")

    # 4. Final KMeans Execution (k=5)
    print("[*] Executing KMeans with k=5...")
    kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(X_scaled)

    # Calculate distance from centroid for each point
    distances = kmeans.transform(X_scaled)
    min_distances = np.min(distances, axis=1)

    # Compile Results
    data["cluster_id"] = cluster_labels
    data["cluster_name"] = data["cluster_id"].apply(
        lambda x: f"Archetype_{x}"
    )  # Temporary, Day 37 refines this
    data["distance_from_centroid"] = min_distances

    output_cols = ["company_id", "cluster_id", "cluster_name", "distance_from_centroid"]
    results_df = data[output_cols].copy()

    csv_path = output_dir / "cluster_labels.csv"
    results_df.to_csv(csv_path, index=False)

    print(f"[✓] Assigned {len(results_df)} companies to 5 clusters.")
    print(f"[✓] Saved clustering results -> {csv_path}")


if __name__ == "__main__":
    run_clustering()
