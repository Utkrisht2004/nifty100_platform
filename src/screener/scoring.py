import pandas as pd


def winsorize_and_scale(series, invert=False):
    """Caps at P10/P90 and scales to 0-100."""
    s = series.dropna()
    if s.empty or len(s) < 2:
        return pd.Series(50, index=series.index)

    p10, p90 = s.quantile(0.10), s.quantile(0.90)
    clipped = s.clip(lower=p10, upper=p90)

    min_val, max_val = clipped.min(), clipped.max()
    if max_val == min_val:
        scaled = pd.Series(50, index=clipped.index)
    else:
        if invert:
            scaled = (max_val - clipped) / (max_val - min_val) * 100
        else:
            scaled = (clipped - min_val) / (max_val - min_val) * 100

    # Reindex to match original including NaNs (NaNs will remain NaN)
    return pd.Series(scaled, index=clipped.index).reindex(series.index)


def calculate_composite_score(df):
    """Calculates the weighted 0-100 composite quality score."""
    scores = pd.DataFrame(index=df.index)

    # 1. Profitability (35%)
    scores["roe_score"] = winsorize_and_scale(df["return_on_equity_pct"]) * 0.15
    scores["roce_score"] = winsorize_and_scale(df["roce_pct"]) * 0.10
    scores["npm_score"] = winsorize_and_scale(df["net_profit_margin_pct"]) * 0.10

    # 2. Cash Quality (30%)
    # Using fcf_conversion as a proxy for FCF CAGR which isn't in our DB
    scores["fcf_score"] = winsorize_and_scale(df["fcf_conversion_pct"]) * 0.15

    # Handle categorical CFO Quality
    cfo_map = {"High Quality": 100, "Moderate": 50, "Accrual Risk": 0}
    scores["cfo_pat_score"] = df["cfo_quality_label"].map(cfo_map).fillna(50) * 0.10
    scores["fcf_pos_score"] = (df["free_cash_flow_cr"] > 0).astype(int) * 100 * 0.05

    # 3. Growth (20%)
    scores["rev_growth_score"] = winsorize_and_scale(df["revenue_cagr_5yr"]) * 0.10
    scores["pat_growth_score"] = winsorize_and_scale(df["pat_cagr_5yr"]) * 0.10

    # 4. Leverage (15%) - Invert D/E so lower is better
    scores["de_score"] = winsorize_and_scale(df["debt_to_equity"], invert=True) * 0.10
    scores["icr_score"] = winsorize_and_scale(df["interest_coverage"]) * 0.05

    # Sum up the components
    df["composite_quality_score"] = scores.sum(axis=1)

    # Sector-Relative Normalization
    df["sector_relative_score"] = df.groupby("broad_sector")[
        "composite_quality_score"
    ].transform(lambda x: winsorize_and_scale(x))

    return df
