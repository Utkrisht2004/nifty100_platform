import pytest


# Mock KPI calculation functions based on Sprint 2/3 logic
def calc_roe(net_profit, equity):
    if equity <= 0:
        return None
    return (net_profit / equity) * 100


def calc_de(debt, equity):
    if equity <= 0:
        return None
    if debt == 0:
        return 0.0
    return debt / equity


def calc_icr(ebit, interest):
    if interest == 0:
        return None
    return ebit / interest


# 20 KPI Unit Tests using parameterization
@pytest.mark.parametrize(
    "np, eq, expected",
    [
        (100, 1000, 10.0),
        (50, 500, 10.0),
        (-50, 1000, -5.0),
        (0, 1000, 0.0),
        (200, 1000, 20.0),  # 5 standard ROE
        (100, 0, None),
        (100, -500, None),
        (-50, -500, None),
        (0, 0, None),
        (50, -100, None),  # 5 negative/zero equity ROE
    ],
)
def test_calc_roe(np, eq, expected):
    """Test ROE calculations including negative equity safety"""
    assert calc_roe(np, eq) == expected


@pytest.mark.parametrize(
    "debt, eq, expected",
    [
        (0, 1000, 0.0),
        (0, 500, 0.0),
        (500, 1000, 0.5),
        (1000, 500, 2.0),
        (250, 1000, 0.25),  # 5 D/E tests including debt-free
    ],
)
def test_calc_de(debt, eq, expected):
    """Test Debt/Equity calculations including zero debt"""
    assert calc_de(debt, eq) == expected


@pytest.mark.parametrize(
    "ebit, interest, expected",
    [
        (1000, 0, None),
        (500, 0, None),
        (1000, 100, 10.0),
        (500, 50, 10.0),
        (-100, 10, -10.0),  # 5 ICR tests including zero interest
    ],
)
def test_calc_icr(ebit, interest, expected):
    """Test Interest Coverage Ratio including zero interest safety"""
    assert calc_icr(ebit, interest) == expected
