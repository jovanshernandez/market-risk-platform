from __future__ import annotations

import time
from collections import Counter
from typing import Any

from fastapi import FastAPI, Request, Response

from market_risk_platform.cli import build_portfolio_risk
from market_risk_platform.pricing import price_fx_option
from market_risk_platform.sample_data import FX_POSITIONS

app = FastAPI(
    title="Market Risk Platform",
    description="Production-style API for market data and portfolio risk workloads.",
    version="0.1.0",
)

START_TIME = time.time()
REQUEST_COUNTS: Counter[tuple[str, str, int]] = Counter()


@app.middleware("http")
async def count_requests(request: Request, call_next):
    response = await call_next(request)
    REQUEST_COUNTS[(request.method, request.url.path, response.status_code)] += 1
    return response


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/metrics")
def metrics() -> Response:
    portfolio = build_portfolio_risk()
    fx_results = [price_fx_option(position) for position in FX_POSITIONS]

    lines = [
        "# HELP market_risk_platform_up API process health.",
        "# TYPE market_risk_platform_up gauge",
        "market_risk_platform_up 1",
        "# HELP market_risk_http_requests_total HTTP requests handled by the API.",
        "# TYPE market_risk_http_requests_total counter",
    ]
    for (method, path, status), count in sorted(REQUEST_COUNTS.items()):
        lines.append(
            f'market_risk_http_requests_total{{method="{method}",path="{path}",status="{status}"}} {count}'
        )
    lines.extend(
        [
            "# HELP market_risk_portfolio_beta Portfolio beta by symbol.",
            "# TYPE market_risk_portfolio_beta gauge",
        ]
    )
    for symbol, beta in portfolio["betas"].items():
        lines.append(f'market_risk_portfolio_beta{{symbol="{symbol}"}} {beta}')
    lines.extend(
        [
            "# HELP market_risk_portfolio_sharpe Annualized portfolio Sharpe ratio.",
            "# TYPE market_risk_portfolio_sharpe gauge",
            f"market_risk_portfolio_sharpe {portfolio['sharpe']}",
            "# HELP market_risk_portfolio_var_95_10d Portfolio 95 percent 10 day value at risk.",
            "# TYPE market_risk_portfolio_var_95_10d gauge",
            f"market_risk_portfolio_var_95_10d {portfolio['var_95_10d']['value_at_risk']}",
            "# HELP market_risk_portfolio_expected_shortfall_95_10d Portfolio 95 percent 10 day expected shortfall.",
            "# TYPE market_risk_portfolio_expected_shortfall_95_10d gauge",
            f"market_risk_portfolio_expected_shortfall_95_10d {portfolio['var_95_10d']['expected_shortfall']}",
            "# HELP market_risk_portfolio_mean_pnl Simulated mean portfolio PnL.",
            "# TYPE market_risk_portfolio_mean_pnl gauge",
            f"market_risk_portfolio_mean_pnl {portfolio['var_95_10d']['mean_pnl']}",
            "# HELP market_risk_fx_option_price FX option model price by symbol.",
            "# TYPE market_risk_fx_option_price gauge",
        ]
    )
    for result in fx_results:
        lines.append(f'market_risk_fx_option_price{{symbol="{result.symbol}"}} {result.price}')
    lines.extend(
        [
            "# HELP market_risk_fx_option_delta FX option delta by symbol.",
            "# TYPE market_risk_fx_option_delta gauge",
        ]
    )
    for result in fx_results:
        lines.append(f'market_risk_fx_option_delta{{symbol="{result.symbol}"}} {result.delta}')
    lines.extend(
        [
            "# HELP market_risk_fx_option_vega FX option vega by symbol.",
            "# TYPE market_risk_fx_option_vega gauge",
        ]
    )
    for result in fx_results:
        lines.append(f'market_risk_fx_option_vega{{symbol="{result.symbol}"}} {result.vega}')
    lines.extend(
        [
            "# HELP market_risk_fx_option_notional_value FX option notional model value by symbol.",
            "# TYPE market_risk_fx_option_notional_value gauge",
        ]
    )
    for result in fx_results:
        lines.append(f'market_risk_fx_option_notional_value{{symbol="{result.symbol}"}} {result.notional_value}')
    lines.extend(
        [
            "# HELP quant_risk_last_success_timestamp_seconds Last successful sample risk calculation.",
            "# TYPE quant_risk_last_success_timestamp_seconds gauge",
            f"quant_risk_last_success_timestamp_seconds {int(START_TIME)}",
            "",
        ]
    )
    body = "\n".join(lines)
    return Response(content=body, media_type="text/plain")


@app.get("/risk/fx-options")
def fx_option_risk() -> list[dict[str, Any]]:
    return [price_fx_option(position).__dict__ for position in FX_POSITIONS]


@app.get("/risk/portfolio")
def portfolio_risk() -> dict[str, object]:
    return build_portfolio_risk()
