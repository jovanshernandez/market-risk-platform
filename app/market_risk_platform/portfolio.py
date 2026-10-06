"""Portfolio statistics: beta, Sharpe ratio, and Monte Carlo VaR / expected shortfall."""

from __future__ import annotations

import math
import random
from collections.abc import Sequence
from dataclasses import dataclass
from statistics import mean, pstdev

TRADING_DAYS_PER_YEAR = 252


@dataclass(frozen=True)
class ReturnSeries:
    symbol: str
    daily_returns: list[float]


def calculate_beta(asset_returns: Sequence[float], benchmark_returns: Sequence[float]) -> float:
    """Beta = cov(asset, benchmark) / var(benchmark), using sample (n-1) estimators."""
    if len(asset_returns) != len(benchmark_returns):
        raise ValueError("asset and benchmark return series must be the same length")
    if len(asset_returns) < 2:
        raise ValueError("at least two observations are required")

    asset_mean = mean(asset_returns)
    benchmark_mean = mean(benchmark_returns)
    covariance = sum(
        (asset - asset_mean) * (benchmark - benchmark_mean)
        for asset, benchmark in zip(asset_returns, benchmark_returns)
    ) / (len(asset_returns) - 1)
    benchmark_variance = sum((value - benchmark_mean) ** 2 for value in benchmark_returns) / (
        len(benchmark_returns) - 1
    )
    if benchmark_variance == 0:
        raise ValueError("benchmark variance cannot be zero")
    return covariance / benchmark_variance


def weighted_returns(series: Sequence[ReturnSeries], weights: Sequence[float]) -> list[float]:
    """Daily portfolio returns for fixed weights (rebalanced daily)."""
    if not series:
        raise ValueError("at least one return series is required")
    if len(series) != len(weights):
        raise ValueError("one weight is required per return series")
    length = len(series[0].daily_returns)
    if any(len(item.daily_returns) != length for item in series):
        raise ValueError("all return series must be the same length")
    return [
        sum(weight * item.daily_returns[index] for item, weight in zip(series, weights))
        for index in range(length)
    ]


def monte_carlo_var(
    current_value: float,
    daily_returns: Sequence[float],
    horizon_days: int = 10,
    confidence: float = 0.95,
    simulations: int = 10_000,
    seed: int = 7,
) -> dict[str, float]:
    """Simulate horizon PnL from a normal model fitted to ``daily_returns``.

    Each path compounds ``horizon_days`` normal daily returns. Value at risk is
    the loss at the ``1 - confidence`` quantile of simulated PnL; expected
    shortfall is the average loss across that same tail. Both are reported as
    positive loss amounts (zero if the tail is profitable).
    """
    if current_value <= 0:
        raise ValueError("current_value must be positive")
    if not 0 < confidence < 1:
        raise ValueError("confidence must be between 0 and 1")
    if horizon_days <= 0 or simulations <= 0:
        raise ValueError("horizon_days and simulations must be positive")
    if len(daily_returns) < 2:
        raise ValueError("at least two returns are required")

    mu = mean(daily_returns)
    sigma = pstdev(daily_returns)
    rng = random.Random(seed)

    pnl_samples: list[float] = []
    for _ in range(simulations):
        terminal_value = current_value
        for _ in range(horizon_days):
            terminal_value *= 1 + rng.gauss(mu, sigma)
        pnl_samples.append(terminal_value - current_value)

    pnl_samples.sort()
    # Number of worst outcomes in the tail. round() guards against float noise
    # such as (1 - 0.95) * 2000 == 100.00000000000009.
    tail_count = max(1, math.ceil(round((1 - confidence) * simulations, 9)))
    tail = pnl_samples[:tail_count]

    return {
        "value_at_risk": max(0.0, -tail[-1]),
        "expected_shortfall": max(0.0, -mean(tail)),
        "mean_pnl": mean(pnl_samples),
        "pnl_volatility": pstdev(pnl_samples),
    }


def annualized_sharpe(daily_returns: Sequence[float], risk_free_rate: float = 0.0) -> float:
    """sqrt(252) * mean(excess daily return) / stdev(excess daily return)."""
    if len(daily_returns) < 2:
        raise ValueError("at least two returns are required")
    daily_risk_free = risk_free_rate / TRADING_DAYS_PER_YEAR
    excess = [value - daily_risk_free for value in daily_returns]
    volatility = pstdev(excess)
    if math.isclose(volatility, 0.0):
        raise ValueError("return volatility cannot be zero")
    return math.sqrt(TRADING_DAYS_PER_YEAR) * mean(excess) / volatility
