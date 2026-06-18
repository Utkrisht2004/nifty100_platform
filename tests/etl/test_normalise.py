import pytest
import pandas as pd
from src.etl.normaliser import normalize_year, normalize_ticker

def test_ticker_strip():
    assert normalize_ticker(pd.Series(["  TCS  "])).iloc[0] == "TCS"

def test_ticker_lower():
    assert normalize_ticker(pd.Series(["tcs"])).iloc[0] == "TCS"

def test_ticker_special_chars():
    assert normalize_ticker(pd.Series(["BAJAJ-AUTO"])).iloc[0] == "BAJAJ-AUTO"
    assert normalize_ticker(pd.Series(["M&M"])).iloc[0] == "M&M"

def test_year_mar23():
    assert normalize_year("Mar-23") == "2023-03"

def test_year_mar_space_23():
    assert normalize_year("Mar 23") == "2023-03"

def test_year_full_march():
    assert normalize_year("March-2023") == "2023-03"

def test_year_integer():
    assert normalize_year("2023") == "2023-03"

def test_year_fy24():
    assert normalize_year("FY24") == "2024-03"

def test_year_dec22():
    assert normalize_year("Dec-22") == "2022-12"

def test_year_garbage():
    assert normalize_year("xyz") == "PARSE ERROR"