"""Risk workloads shared by the API and the CLI."""

from __future__ import annotations

from collections.abc import Sequence

from market_risk_platform.models import FxOptionPosition
from market_risk_platform.portfolio import (
    ReturnSeries,
    annualized_sharpe,
    calculate_beta,
    monte_carlo_var,
    weighted_returns,
)
from market_risk_platform.pricing import price_fx_option
from market_risk_platform.sample_data import ASSET_RETURNS, FX_POSITIONS, SPY_RETURNS
from market_risk_platform.schemas import (
    FxOptionRisk,
    PortfolioRisk,
    PortfolioRiskRequest,
    ValueAtRisk,
)


def fx_option_risk(positions: Sequence[FxOptionPosition] = FX_POSITIONS) -> list[FxOptionRisk]:
    results = []
    for position in positions:
        result = price_fx_option(position)
        results.append(
            FxOptionRisk(
                symbol=result.symbol,
                option_type=result.option_type,
                premium_currency=result.premium_currency,
                price=round(result.price, 6),
                delta=round(result.delta, 6),
                gamma=round(result.gamma, 6),
                vega=round(result.vega, 6),
                theta=round(result.theta, 6),
                notional_value=round(result.notional_value, 2),
            )
        )
    return results


def portfolio_risk(request: PortfolioRiskRequest) -> PortfolioRisk:
    series = [ReturnSeries(asset.symbol, asset.daily_returns) for asset in request.assets]
    weights = [asset.weight for asset in request.assets]

    betas = {item.symbol: calculate_beta(item.daily_returns, request.benchmark_returns) for item in series}
    returns = weighted_returns(series, weights)
    var = monte_carlo_var(
        request.portfolio_value,
        returns,
        horizon_days=request.horizon_days,
        confidence=request.confidence,
        simulations=request.simulations,
        seed=request.seed,
    )

    return PortfolioRisk(
        benchmark=request.benchmark_symbol,
        portfolio_value=request.portfolio_value,
        weights={asset.symbol: round(asset.weight, 6) for asset in request.assets},
        betas={symbol: round(beta, 4) for symbol, beta in betas.items()},
        portfolio_beta=round(sum(betas[item.symbol] * weight for item, weight in zip(series, weights)), 4),
        sharpe=round(annualized_sharpe(returns), 4),
        var=ValueAtRisk(
            confidence=request.confidence,
            horizon_days=request.horizon_days,
            simulations=request.simulations,
            **{key: round(value, 2) for key, value in var.items()},
        ),
    )


def sample_portfolio_request(**overrides: object) -> PortfolioRiskRequest:
    """The bundled sample book: equal-weighted AAPL, MSFT and XLK against SPY."""
    weight = 1.0 / len(ASSET_RETURNS)
    payload: dict[str, object] = {
        "portfolio_value": 1_000_000.0,
        "benchmark_symbol": "SPY",
        "benchmark_returns": SPY_RETURNS,
        "assets": [
            {"symbol": item.symbol, "weight": weight, "daily_returns": item.daily_returns}
            for item in ASSET_RETURNS
        ],
        "confidence": 0.95,
        "horizon_days": 10,
        "simulations": 2_000,
        "seed": 7,
    }
    payload.update(overrides)
    return PortfolioRiskRequest.model_validate(payload)


def sample_portfolio_risk() -> PortfolioRisk:
    return portfolio_risk(sample_portfolio_request())
