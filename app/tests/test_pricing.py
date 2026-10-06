import math
from dataclasses import replace

import pytest

from market_risk_platform.models import FxOptionPosition, OptionType
from market_risk_platform.pricing import price_fx_option

EURUSD_CALL = FxOptionPosition("EURUSD", 1.10, 1.15, 0.25, 0.02, 0.01, 0.12, OptionType.CALL)


def test_matches_textbook_reference_value():
    # Hull, Options, Futures and Other Derivatives: 4-month GBP call, S=K=1.60,
    # r_USD=8%, r_GBP=11%, vol=14.1% is worth about 4.3 cents.
    position = FxOptionPosition("GBPUSD", 1.60, 1.60, 4 / 12, 0.08, 0.11, 0.141, OptionType.CALL)

    assert price_fx_option(position).price == pytest.approx(0.043, abs=0.0005)


def test_put_call_parity_holds():
    call = price_fx_option(EURUSD_CALL)
    put = price_fx_option(replace(EURUSD_CALL, option_type=OptionType.PUT))
    p = EURUSD_CALL
    forward_value = p.spot * math.exp(-p.foreign_rate * p.maturity_years) - p.strike * math.exp(
        -p.domestic_rate * p.maturity_years
    )

    assert call.price - put.price == pytest.approx(forward_value, abs=1e-12)


@pytest.mark.parametrize("option_type", [OptionType.CALL, OptionType.PUT])
def test_greeks_match_finite_differences(option_type):
    base = replace(EURUSD_CALL, option_type=option_type)
    result = price_fx_option(base)

    def price(**changes):
        return price_fx_option(replace(base, **changes)).price

    h = 1e-4
    delta = (price(spot=base.spot + h) - price(spot=base.spot - h)) / (2 * h)
    gamma = (price(spot=base.spot + h) - 2 * result.price + price(spot=base.spot - h)) / h**2
    vega_per_point = (price(volatility=base.volatility + h) - price(volatility=base.volatility - h)) / (2 * h) / 100
    one_day = 1 / 365
    theta_per_day = price(maturity_years=base.maturity_years - one_day) - result.price

    assert result.delta == pytest.approx(delta, rel=1e-6)
    assert result.gamma == pytest.approx(gamma, rel=1e-4)
    assert result.vega == pytest.approx(vega_per_point, rel=1e-6)
    assert result.theta == pytest.approx(theta_per_day, rel=1e-2)


def test_call_and_put_signs():
    call = price_fx_option(EURUSD_CALL)
    put = price_fx_option(FxOptionPosition("USDJPY", 135.0, 130.0, 0.50, 0.015, 0.005, 0.10, OptionType.PUT))

    assert 0.0 < call.delta < 1.0
    assert -1.0 < put.delta < 0.0
    assert call.gamma > 0 and put.gamma > 0
    assert call.vega > 0 and put.vega > 0


def test_premium_is_in_quote_currency():
    result = price_fx_option(replace(EURUSD_CALL, notional=2_500_000))

    assert result.premium_currency == "USD"
    assert result.notional_value == pytest.approx(result.price * 2_500_000)


@pytest.mark.parametrize(
    "changes",
    [{"spot": 0.0}, {"strike": -1.0}, {"maturity_years": 0.0}, {"volatility": 0.0}],
)
def test_rejects_invalid_inputs(changes):
    with pytest.raises(ValueError):
        price_fx_option(replace(EURUSD_CALL, **changes))
