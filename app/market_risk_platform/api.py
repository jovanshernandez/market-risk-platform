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
