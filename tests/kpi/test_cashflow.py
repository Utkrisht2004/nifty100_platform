import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../../')))
from src.analytics.cashflow_kpis import (
    calc_free_cash_flow,
    calc_cfo_quality_score,
    calc_capex_intensity,
    calc_fcf_conversion,
    classify_capital_allocation
)

def test_fcf_calculation():
    assert calc_free_cash_flow(operating_activity=100, investing_activity=-40) == 60

def test_cfo_quality_high():
    score, label = calc_cfo_quality_score(cfo=120, pat=100)
    assert score == 1.2
    assert label == "High Quality"

def test_cfo_quality_accrual_risk():
    score, label = calc_cfo_quality_score(cfo=30, pat=100)
    assert score == 0.3
    assert label == "Accrual Risk"

def test_cfo_quality_zero_pat():
    score, label = calc_cfo_quality_score(cfo=100, pat=0)
    assert score is None
    assert label is None

def test_capex_intensity_asset_light():
    intensity, label = calc_capex_intensity(cfi=-20, sales=1000)
    assert intensity == 2.0
    assert label == "Asset Light"

def test_fcf_conversion():
    assert calc_fcf_conversion(fcf=50, operating_profit=100) == 50.0
    assert calc_fcf_conversion(fcf=50, operating_profit=0) is None

def test_capital_allocation_reinvestor():
    assert classify_capital_allocation(100, -50, -20) == "Reinvestor"

def test_capital_allocation_shareholder_returns():
    assert classify_capital_allocation(100, -50, -20, "High Quality") == "Shareholder Returns"

def test_capital_allocation_distress():
    assert classify_capital_allocation(-10, 50, 20) == "Distress Signal"
