import math

from market_risk_platform.models import FxOptionPosition, OptionType, RiskResult


def _normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def _normal_pdf(value: float) -> float:
    return math.exp(-0.5 * value * value) / math.sqrt(2.0 * math.pi)


def price_fx_option(position: FxOptionPosition) -> RiskResult:
    """Price an FX option with Garman-Kohlhagen and return core Greeks."""
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

    d1 = (
        math.log(spot / strike)
        + (rd - rf + 0.5 * vol * vol) * maturity
    ) / (vol * sqrt_t)
    d2 = d1 - vol * sqrt_t

    domestic_discount = math.exp(-rd * maturity)
    foreign_discount = math.exp(-rf * maturity)

    if position.option_type == OptionType.CALL:
        price = spot * foreign_discount * _normal_cdf(d1) - strike * domestic_discount * _normal_cdf(d2)
        delta = foreign_discount * _normal_cdf(d1)
        theta = (
            -(spot * foreign_discount * _normal_pdf(d1) * vol) / (2 * sqrt_t)
            + rf * spot * foreign_discount * _normal_cdf(d1)
            - rd * strike * domestic_discount * _normal_cdf(d2)
        )
    elif position.option_type == OptionType.PUT:
        price = strike * domestic_discount * _normal_cdf(-d2) - spot * foreign_discount * _normal_cdf(-d1)
        delta = -foreign_discount * _normal_cdf(-d1)
        theta = (
            -(spot * foreign_discount * _normal_pdf(d1) * vol) / (2 * sqrt_t)
            - rf * spot * foreign_discount * _normal_cdf(-d1)
            + rd * strike * domestic_discount * _normal_cdf(-d2)
        )
    else:
        raise ValueError(f"unsupported option type: {position.option_type}")

    gamma = foreign_discount * _normal_pdf(d1) / (spot * vol * sqrt_t)
    vega = spot * foreign_discount * _normal_pdf(d1) * sqrt_t
    notional_value = price * position.notional

    return RiskResult(
        symbol=position.symbol,
        price=price,
        delta=delta,
        gamma=gamma,
        vega=vega,
        theta=theta / 365.0,
        notional_value=notional_value,
    )

