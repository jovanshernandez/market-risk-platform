from __future__ import annotations

import math
import random
from dataclasses import dataclass
from statistics import mean, pstdev


@dataclass(frozen=True)
class ReturnSeries:
    symbol: str
    daily_returns: list[float]


def calculate_beta(asset_returns: list[float], benchmark_returns: list[float]) -> float:
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
    benchmark_variance = sum((value - benchmark_mean) ** 2 for value in benchmark_returns) / (len(benchmark_returns) - 1)
    if benchmark_variance == 0:
        raise ValueError("benchmark variance cannot be zero")
    return covariance / benchmark_variance


def monte_carlo_var(
    current_value: float,
    daily_returns: list[float],
    horizon_days: int = 10,
    confidence: float = 0.95,
    simulations: int = 10_000,
    seed: int = 7,
) -> dict[str, float]:
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
    tail_index = max(0, int((1 - confidence) * simulations) - 1)
    var_amount = abs(min(0.0, pnl_samples[tail_index]))
    expected_shortfall = abs(mean([sample for sample in pnl_samples[: tail_index + 1] if sample < 0] or [0.0]))

    return {
        "value_at_risk": var_amount,
        "expected_shortfall": expected_shortfall,
        "mean_pnl": mean(pnl_samples),
        "pnl_volatility": pstdev(pnl_samples),
    }


def annualized_sharpe(daily_returns: list[float], risk_free_rate: float = 0.0) -> float:
    if len(daily_returns) < 2:
        raise ValueError("at least two returns are required")
    daily_risk_free = risk_free_rate / 252
    excess = [value - daily_risk_free for value in daily_returns]
    volatility = pstdev(excess)
    if math.isclose(volatility, 0.0):
        raise ValueError("return volatility cannot be zero")
    return math.sqrt(252) * mean(excess) / volatility

