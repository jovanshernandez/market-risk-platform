"""FastAPI service exposing FX option and portfolio risk, health checks, and Prometheus metrics."""

from __future__ import annotations

import math
import time

from fastapi import Body, FastAPI, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.routing import Match

from market_risk_platform import __version__
from market_risk_platform.metrics import REGISTRY, observe_request, refresh_risk_metrics
from market_risk_platform.risk import fx_option_risk, portfolio_risk, sample_portfolio_risk
from market_risk_platform.schemas import (
    FxOptionRequest,
    FxOptionRisk,
    Health,
    PortfolioRisk,
    PortfolioRiskRequest,
    Readiness,
)

app = FastAPI(
    title="Market Risk Platform",
    description=(
        "FX option pricing (Garman-Kohlhagen) and portfolio risk (beta, Sharpe, Monte Carlo VaR "
        "and expected shortfall), with health, readiness and Prometheus metrics endpoints."
    ),
    version=__version__,
    openapi_tags=[
        {"name": "risk", "description": "Pricing and portfolio risk calculations."},
        {"name": "ops", "description": "Health, readiness and metrics for deploy gates and monitoring."},
    ],
)


@app.middleware("http")
async def record_request_metrics(request: Request, call_next):
    started = time.perf_counter()
    status = 500
    try:
        response = await call_next(request)
        status = response.status_code
        return response
    finally:
        observe_request(request.method, _route_template(request), status, time.perf_counter() - started)


def _route_template(request: Request) -> str:
    """Label requests by route template, not raw URL, so unknown paths can't explode label cardinality."""
    route = request.scope.get("route")
    if route is not None:
        return route.path
    # Plain Starlette routes (/docs, /openapi.json) don't record themselves in the scope.
    for candidate in request.app.router.routes:
        match, _ = candidate.matches(request.scope)
        if match == Match.FULL:
            return getattr(candidate, "path", "unmatched")
    return "unmatched"


@app.get("/health", response_model=Health, tags=["ops"], summary="Liveness check")
def health() -> Health:
    """Liveness: the process is up and serving requests."""
    return Health()


@app.get("/ready", response_model=Readiness, tags=["ops"], summary="Readiness check", responses={503: {"model": Readiness}})
def ready() -> Response | Readiness:
    """Readiness: run the sample risk workloads and check the results are usable."""
    try:
        portfolio = sample_portfolio_risk()
        options = fx_option_risk()
        checks = {
            "portfolio_risk": math.isfinite(portfolio.var.value_at_risk) and portfolio.var.value_at_risk > 0,
            "fx_option_risk": len(options) > 0 and all(math.isfinite(option.price) for option in options),
        }
    except Exception:
        checks = {"portfolio_risk": False, "fx_option_risk": False}

    readiness = Readiness(status="ready" if all(checks.values()) else "not_ready", checks=checks)
    if readiness.status != "ready":
        return JSONResponse(status_code=503, content=readiness.model_dump())
    return readiness


@app.get("/metrics", tags=["ops"], response_class=Response, summary="Prometheus metrics")
def metrics() -> Response:
    """Prometheus exposition: request telemetry plus the sample book's risk numbers."""
    refresh_risk_metrics()
    return Response(content=generate_latest(REGISTRY), media_type=CONTENT_TYPE_LATEST)


@app.get("/risk/fx-options", response_model=list[FxOptionRisk], tags=["risk"], summary="Sample FX option book")
def sample_fx_option_risk() -> list[FxOptionRisk]:
    """Price and Greeks for the bundled sample FX option book."""
    return fx_option_risk()


@app.post("/risk/fx-options", response_model=list[FxOptionRisk], tags=["risk"], summary="Price FX options")
def price_fx_options(
    options: list[FxOptionRequest] = Body(min_length=1, max_length=500),
) -> list[FxOptionRisk]:
    """Price a list of European FX options with Garman-Kohlhagen."""
    return fx_option_risk([option.to_position() for option in options])


@app.get("/risk/portfolio", response_model=PortfolioRisk, tags=["risk"], summary="Sample portfolio risk")
def sample_portfolio() -> PortfolioRisk:
    """Beta, Sharpe and 10-day 95% Monte Carlo VaR for the bundled sample portfolio."""
    return sample_portfolio_risk()


@app.post("/risk/portfolio", response_model=PortfolioRisk, tags=["risk"], summary="Custom portfolio risk")
def custom_portfolio(request: PortfolioRiskRequest) -> PortfolioRisk:
    """Beta, Sharpe, VaR and expected shortfall for a portfolio you supply."""
    return portfolio_risk(request)
