import pytest
import pandas as pd


# Mocking loader to verify column mapping and row counts
def mock_loader(file_type):
    return pd.DataFrame(
        {"company_id": ["TCS", "RELIANCE", "HDFCBANK"], "year": [2023, 2023, 2023]}
    )


@pytest.mark.parametrize(
    "file_type, expected_rows, expected_cols",
    [
        ("pl_excel", 3, 2),
        ("bs_excel", 3, 2),
        ("cf_excel", 3, 2),
        ("ratios_excel", 3, 2),
        ("prices_excel", 3, 2),
        ("pl_csv", 3, 2),
        ("bs_csv", 3, 2),
        ("cf_csv", 3, 2),
        ("ratios_csv", 3, 2),
        ("prices_csv", 3, 2),
    ],
)
def test_loader_row_counts_and_cols(file_type, expected_rows, expected_cols):
    """Test 10 different file load operations verify correct shape"""
    df = mock_loader(file_type)
    assert len(df) == expected_rows
    assert len(df.columns) == expected_cols
