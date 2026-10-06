"""Prometheus metrics for the API: request telemetry plus the sample book's risk numbers."""

from __future__ import annotations

import time

from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram, disable_created_metrics

from market_risk_platform.risk import fx_option_risk, sample_portfolio_risk

disable_created_metrics()

REGISTRY = CollectorRegistry()

UP = Gauge("market_risk_platform_up", "API process health.", registry=REGISTRY)
UP.set(1)

HTTP_REQUESTS = Counter(
    "market_risk_http_requests",
    "HTTP requests handled by the API.",
    ["method", "path", "status"],
    registry=REGISTRY,
)
HTTP_LATENCY = Histogram(
    "market_risk_http_request_duration_seconds",
    "HTTP request latency.",
    ["method", "path"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0),
    registry=REGISTRY,
)

PORTFOLIO_BETA = Gauge("market_risk_portfolio_beta", "Portfolio beta by symbol.", ["symbol"], registry=REGISTRY)
PORTFOLIO_SHARPE = Gauge("market_risk_portfolio_sharpe", "Annualized portfolio Sharpe ratio.", registry=REGISTRY)
PORTFOLIO_VAR = Gauge(
    "market_risk_portfolio_var_95_10d", "Portfolio 95 percent 10 day value at risk.", registry=REGISTRY
)
PORTFOLIO_ES = Gauge(
    "market_risk_portfolio_expected_shortfall_95_10d",
    "Portfolio 95 percent 10 day expected shortfall.",
    registry=REGISTRY,
)
PORTFOLIO_MEAN_PNL = Gauge("market_risk_portfolio_mean_pnl", "Simulated mean portfolio PnL.", registry=REGISTRY)

FX_PRICE = Gauge("market_risk_fx_option_price", "FX option model price by symbol.", ["symbol"], registry=REGISTRY)
FX_DELTA = Gauge("market_risk_fx_option_delta", "FX option delta by symbol.", ["symbol"], registry=REGISTRY)
FX_VEGA = Gauge(
    "market_risk_fx_option_vega", "FX option vega per 1 vol point by symbol.", ["symbol"], registry=REGISTRY
)
FX_NOTIONAL_VALUE = Gauge(
    "market_risk_fx_option_notional_value",
    "FX option model value (price x notional) in its premium currency.",
    ["symbol", "currency"],
    registry=REGISTRY,
)

LAST_SUCCESS = Gauge(
    "market_risk_last_success_timestamp_seconds",
    "Unix time of the last successful risk calculation.",
    registry=REGISTRY,
)
CALCULATION_FAILURES = Counter(
    "market_risk_calculation_failures",
    "Risk calculations that raised an error.",
    registry=REGISTRY,
)


def observe_request(method: str, path: str, status: int, duration_seconds: float) -> None:
    HTTP_REQUESTS.labels(method=method, path=path, status=str(status)).inc()
    HTTP_LATENCY.labels(method=method, path=path).observe(duration_seconds)


def refresh_risk_metrics() -> bool:
    """Recompute the sample book and publish it. Returns False if the calculation failed."""
    try:
        portfolio = sample_portfolio_risk()
        options = fx_option_risk()
    except Exception:
        CALCULATION_FAILURES.inc()
        return False

    for symbol, beta in portfolio.betas.items():
        PORTFOLIO_BETA.labels(symbol=symbol).set(beta)
    PORTFOLIO_SHARPE.set(portfolio.sharpe)
    PORTFOLIO_VAR.set(portfolio.var.value_at_risk)
    PORTFOLIO_ES.set(portfolio.var.expected_shortfall)
    PORTFOLIO_MEAN_PNL.set(portfolio.var.mean_pnl)

    for option in options:
        FX_PRICE.labels(symbol=option.symbol).set(option.price)
        FX_DELTA.labels(symbol=option.symbol).set(option.delta)
        FX_VEGA.labels(symbol=option.symbol).set(option.vega)
        FX_NOTIONAL_VALUE.labels(symbol=option.symbol, currency=option.premium_currency).set(option.notional_value)

    LAST_SUCCESS.set(time.time())
    return True
