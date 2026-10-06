"""Pydantic request and response models for the API and CLI."""

from __future__ import annotations

import math
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from market_risk_platform.models import FxOptionPosition, OptionType

# Cap the work a single request can ask for (simulations x horizon days).
MAX_SIMULATION_STEPS = 1_000_000


class Health(BaseModel):
    status: Literal["ok"] = "ok"


class Readiness(BaseModel):
    status: Literal["ready", "not_ready"]
    checks: dict[str, bool]


class FxOptionRequest(BaseModel):
    """A European FX option to price."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "symbol": "EURUSD",
                    "spot": 1.10,
                    "strike": 1.15,
                    "maturity_years": 0.25,
                    "domestic_rate": 0.02,
                    "foreign_rate": 0.01,
                    "volatility": 0.12,
                    "option_type": "call",
                    "notional": 2_500_000,
                }
            ]
        }
    )

    symbol: str = Field(pattern=r"^[A-Z]{6}$", description="Currency pair as BASEQUOTE, e.g. EURUSD.")
    spot: float = Field(gt=0, description="Spot rate, quote currency per unit of base currency.")
    strike: float = Field(gt=0)
    maturity_years: float = Field(gt=0, le=30, description="Time to expiry in years.")
    domestic_rate: float = Field(ge=-0.2, le=1, description="Quote-currency rate, continuously compounded.")
    foreign_rate: float = Field(ge=-0.2, le=1, description="Base-currency rate, continuously compounded.")
    volatility: float = Field(gt=0, le=5, description="Annualized implied volatility, e.g. 0.12 for 12%.")
    option_type: OptionType
    notional: float = Field(default=1_000_000.0, gt=0, description="Notional in base-currency units.")

    def to_position(self) -> FxOptionPosition:
        return FxOptionPosition(**self.model_dump())


class FxOptionRisk(BaseModel):
    symbol: str
    option_type: OptionType
    premium_currency: str = Field(description="Currency of price and notional_value (the quote currency).")
    price: float = Field(description="Premium per unit of base-currency notional.")
    delta: float = Field(description="Spot delta (premium-unadjusted).")
    gamma: float = Field(description="Change in delta per 1.00 move in spot.")
    vega: float = Field(description="Price change per 1 vol point (0.01).")
    theta: float = Field(description="Price change per calendar day.")
    notional_value: float = Field(description="price x notional, in premium_currency.")


class AssetReturns(BaseModel):
    symbol: str = Field(min_length=1, max_length=16)
    weight: float = Field(description="Portfolio weight. Weights must sum to 1; negative means short.")
    daily_returns: list[float] = Field(min_length=2, description="Simple daily returns, oldest first.")


class PortfolioRiskRequest(BaseModel):
    """A portfolio of return series to measure against a benchmark."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "portfolio_value": 1_000_000,
                    "benchmark_symbol": "SPY",
                    "benchmark_returns": [0.004, -0.002, 0.006, 0.001, -0.005, 0.003],
                    "assets": [
                        {"symbol": "AAPL", "weight": 0.6, "daily_returns": [0.006, -0.003, 0.009, 0.002, -0.008, 0.004]},
                        {"symbol": "MSFT", "weight": 0.4, "daily_returns": [0.005, -0.002, 0.007, 0.001, -0.006, 0.004]},
                    ],
                    "confidence": 0.99,
                    "horizon_days": 10,
                    "simulations": 5000,
                    "seed": 7,
                }
            ]
        }
    )

    portfolio_value: float = Field(default=1_000_000.0, gt=0)
    benchmark_symbol: str = Field(default="SPY", min_length=1, max_length=16)
    benchmark_returns: list[float] = Field(min_length=2)
    assets: list[AssetReturns] = Field(min_length=1, max_length=100)
    confidence: float = Field(default=0.95, ge=0.5, lt=1)
    horizon_days: int = Field(default=10, ge=1, le=250)
    simulations: int = Field(default=2_000, ge=100, le=100_000)
    seed: int = 7

    @model_validator(mode="after")
    def _check_consistency(self) -> PortfolioRiskRequest:
        symbols = [asset.symbol for asset in self.assets]
        if len(set(symbols)) != len(symbols):
            raise ValueError("asset symbols must be unique")
        expected = len(self.benchmark_returns)
        for asset in self.assets:
            if len(asset.daily_returns) != expected:
                raise ValueError(
                    f"{asset.symbol} has {len(asset.daily_returns)} returns; benchmark has {expected}"
                )
        if not math.isclose(sum(asset.weight for asset in self.assets), 1.0, abs_tol=1e-6):
            raise ValueError("asset weights must sum to 1")
        if self.simulations * self.horizon_days > MAX_SIMULATION_STEPS:
            raise ValueError(f"simulations x horizon_days must be at most {MAX_SIMULATION_STEPS:,}")
        return self


class ValueAtRisk(BaseModel):
    confidence: float
    horizon_days: int
    simulations: int
    value_at_risk: float = Field(description="Loss at the (1 - confidence) quantile of simulated PnL.")
    expected_shortfall: float = Field(description="Average loss in the same tail.")
    mean_pnl: float
    pnl_volatility: float


class PortfolioRisk(BaseModel):
    benchmark: str
    portfolio_value: float
    weights: dict[str, float]
    betas: dict[str, float]
    portfolio_beta: float = Field(description="Weighted sum of asset betas.")
    sharpe: float = Field(description="Annualized Sharpe ratio of the weighted portfolio (risk-free rate 0).")
    var: ValueAtRisk
