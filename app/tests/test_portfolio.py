from market_risk_platform.portfolio import annualized_sharpe, calculate_beta, monte_carlo_var


def test_calculate_beta_tracks_benchmark_sensitivity():
    benchmark = [0.01, -0.01, 0.02, -0.02, 0.015]
    asset = [value * 1.5 for value in benchmark]

    assert round(calculate_beta(asset, benchmark), 2) == 1.50


def test_monte_carlo_var_is_deterministic_with_seed():
    returns = [0.004, -0.002, 0.006, -0.003, 0.001, 0.002]

    first = monte_carlo_var(1_000_000, returns, simulations=500, seed=42)
    second = monte_carlo_var(1_000_000, returns, simulations=500, seed=42)

    assert first == second
    assert first["value_at_risk"] >= 0


def test_annualized_sharpe_returns_float():
    returns = [0.004, -0.002, 0.006, -0.003, 0.001, 0.002]

    assert isinstance(annualized_sharpe(returns), float)

