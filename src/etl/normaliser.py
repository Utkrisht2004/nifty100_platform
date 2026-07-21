import pandas as pd
import re


def normalize_ticker(ticker_series: pd.Series) -> pd.Series:
    return ticker_series.astype(str).str.strip().str.upper()


def normalize_year(year_val: str) -> str:
    if pd.isna(year_val):
        return "PARSE ERROR"

    year_str = str(year_val).strip()

    # Already formatted correctly
    if re.match(r"^\d{4}-\d{2}$", year_str):
        return year_str

    # Handle pure years or FY format (Fixed order: \d{4} before \d{2})
    pure_year_match = re.match(r"^(?:FY)?(\d{4}|\d{2})$", year_str, flags=re.IGNORECASE)
    if pure_year_match:
        y = pure_year_match.group(1)
        full_year = f"20{y}" if len(y) == 2 else y
        return f"{full_year}-03"

    # Handle Month-Year format (Fixed order: \d{4} before \d{2})
    month_year_match = re.search(r"([A-Za-z]+)[\s-]*(\d{4}|\d{2})", year_str)
    if month_year_match:
        month_str = month_year_match.group(1).lower()
        extracted_year = month_year_match.group(2)
        full_year = (
            f"20{extracted_year}" if len(extracted_year) == 2 else extracted_year
        )

        month_map = {
            "mar": "03",
            "march": "03",
            "jun": "06",
            "june": "06",
            "dec": "12",
            "december": "12",
        }

        mapped_month = month_map.get(month_str[:3], None)
        if mapped_month:
            return f"{full_year}-{mapped_month}"

    return "PARSE ERROR"


def apply_year_normalization(year_series: pd.Series) -> pd.Series:
    return year_series.apply(normalize_year)
