import math
from statistics import NormalDist

import pytest

from market_risk_platform.portfolio import (
    ReturnSeries,
    annualized_sharpe,
    calculate_beta,
    monte_carlo_var,
    weighted_returns,
)

RETURNS = [0.004, -0.002, 0.006, -0.003, 0.001, 0.002]


def test_beta_tracks_benchmark_sensitivity():
    benchmark = [0.01, -0.01, 0.02, -0.02, 0.015]
    asset = [value * 1.5 for value in benchmark]

    assert calculate_beta(asset, benchmark) == pytest.approx(1.5)


def test_beta_rejects_mismatched_series():
    with pytest.raises(ValueError):
        calculate_beta([0.01, 0.02], [0.01, 0.02, 0.03])


def test_weighted_returns():
    series = [ReturnSeries("A", [0.01, 0.02]), ReturnSeries("B", [0.03, -0.02])]

    assert weighted_returns(series, [0.25, 0.75]) == pytest.approx([0.025, -0.01])


def test_monte_carlo_var_is_deterministic_with_seed():
    first = monte_carlo_var(1_000_000, RETURNS, simulations=500, seed=42)
    second = monte_carlo_var(1_000_000, RETURNS, simulations=500, seed=42)

    assert first == second


def test_expected_shortfall_is_at_least_var():
    result = monte_carlo_var(1_000_000, RETURNS, simulations=2_000)

    assert result["value_at_risk"] > 0
    assert result["expected_shortfall"] >= result["value_at_risk"]


def test_monte_carlo_var_converges_to_normal_approximation():
    # Zero-drift returns with a known stdev: 10-day 99% VaR should be close to
    # value * z(0.99) * sigma * sqrt(10).
    returns = [0.01, -0.01] * 10
    sigma = 0.01
    result = monte_carlo_var(1_000_000, returns, horizon_days=10, confidence=0.99, simulations=20_000)
    expected = 1_000_000 * NormalDist().inv_cdf(0.99) * sigma * math.sqrt(10)

    assert result["value_at_risk"] == pytest.approx(expected, rel=0.05)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"current_value": 0},
        {"confidence": 1.0},
        {"horizon_days": 0},
        {"simulations": 0},
    ],
)
def test_monte_carlo_var_validates_inputs(kwargs):
    params = {"current_value": 1_000_000, "daily_returns": RETURNS} | kwargs
    with pytest.raises(ValueError):
        monte_carlo_var(**params)


def test_annualized_sharpe():
    returns = [0.002, 0.0, 0.002, 0.0]
    # mean 0.001, population stdev 0.001 -> sqrt(252)
    assert annualized_sharpe(returns) == pytest.approx(math.sqrt(252))
