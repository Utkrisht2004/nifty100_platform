import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from src.analytics.cagr import calculate_cagr


def test_cagr_normal_growth():
    val, flag = calculate_cagr(start_val=100, end_val=150, periods=5)
    assert round(val, 2) == 8.45
    assert flag is None


def test_cagr_normal_decline():
    val, flag = calculate_cagr(start_val=100, end_val=50, periods=5)
    assert round(val, 2) == -12.94
    assert flag is None


def test_cagr_flat_growth():
    val, flag = calculate_cagr(start_val=100, end_val=100, periods=5)
    assert val == 0.0
    assert flag is None


def test_cagr_insufficient_periods():
    val, flag = calculate_cagr(start_val=100, end_val=150, periods=0)
    assert val is None
    assert flag == "INSUFFICIENT"


def test_cagr_none_periods():
    val, flag = calculate_cagr(start_val=100, end_val=150, periods=None)
    assert val is None
    assert flag == "INSUFFICIENT"


def test_cagr_zero_base():
    val, flag = calculate_cagr(start_val=0, end_val=100, periods=3)
    assert val is None
    assert flag == "ZERO_BASE"


def test_cagr_turnaround():
    val, flag = calculate_cagr(start_val=-50, end_val=100, periods=3)
    assert val is None
    assert flag == "TURNAROUND"


def test_cagr_decline_to_loss():
    val, flag = calculate_cagr(start_val=100, end_val=-50, periods=3)
    assert val is None
    assert flag == "DECLINE_TO_LOSS"


def test_cagr_both_negative():
    val, flag = calculate_cagr(start_val=-50, end_val=-10, periods=3)
    assert val is None
    assert flag == "BOTH_NEGATIVE"


def test_cagr_large_numbers():
    val, flag = calculate_cagr(start_val=1000000, end_val=2000000, periods=10)
    assert round(val, 2) == 7.18
    assert flag is None
