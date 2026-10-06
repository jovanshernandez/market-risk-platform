"""Garman-Kohlhagen pricing for European FX options."""

from __future__ import annotations

import math

from market_risk_platform.models import FxOptionPosition, OptionType, RiskResult


def _normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def _normal_pdf(value: float) -> float:
    return math.exp(-0.5 * value * value) / math.sqrt(2.0 * math.pi)


def price_fx_option(position: FxOptionPosition) -> RiskResult:
    """Price an FX option with Garman-Kohlhagen and return its core Greeks.

    Garman-Kohlhagen is Black-Scholes with the foreign interest rate playing the
    role of a continuous dividend yield: holding the base currency earns ``rf``.
    """
    if position.spot <= 0 or position.strike <= 0:
        raise ValueError("spot and strike must be positive")
    if position.maturity_years <= 0:
        raise ValueError("maturity_years must be positive")
    if position.volatility <= 0:
        raise ValueError("volatility must be positive")

    spot = position.spot
    strike = position.strike
    maturity = position.maturity_years
    rd = position.domestic_rate
    rf = position.foreign_rate
    vol = position.volatility
    sqrt_t = math.sqrt(maturity)

    d1 = (math.log(spot / strike) + (rd - rf + 0.5 * vol * vol) * maturity) / (vol * sqrt_t)
    d2 = d1 - vol * sqrt_t

    domestic_discount = math.exp(-rd * maturity)
    foreign_discount = math.exp(-rf * maturity)
    time_decay = -(spot * foreign_discount * _normal_pdf(d1) * vol) / (2 * sqrt_t)

    if position.option_type == OptionType.CALL:
        price = spot * foreign_discount * _normal_cdf(d1) - strike * domestic_discount * _normal_cdf(d2)
        delta = foreign_discount * _normal_cdf(d1)
        theta_per_year = (
            time_decay
            + rf * spot * foreign_discount * _normal_cdf(d1)
            - rd * strike * domestic_discount * _normal_cdf(d2)
        )
    elif position.option_type == OptionType.PUT:
        price = strike * domestic_discount * _normal_cdf(-d2) - spot * foreign_discount * _normal_cdf(-d1)
        delta = -foreign_discount * _normal_cdf(-d1)
        theta_per_year = (
            time_decay
            - rf * spot * foreign_discount * _normal_cdf(-d1)
            + rd * strike * domestic_discount * _normal_cdf(-d2)
        )
    else:  # pragma: no cover - OptionType is a closed enum
        raise ValueError(f"unsupported option type: {position.option_type}")

    gamma = foreign_discount * _normal_pdf(d1) / (spot * vol * sqrt_t)
    vega_per_unit_vol = spot * foreign_discount * _normal_pdf(d1) * sqrt_t

    return RiskResult(
        symbol=position.symbol,
        option_type=position.option_type,
        premium_currency=position.premium_currency,
        price=price,
        delta=delta,
        gamma=gamma,
        vega=vega_per_unit_vol / 100.0,
        theta=theta_per_year / 365.0,
        notional_value=price * position.notional,
    )
