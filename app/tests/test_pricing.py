from market_risk_platform.models import FxOptionPosition, OptionType
from market_risk_platform.pricing import price_fx_option


def test_fx_call_price_and_greeks_are_reasonable():
    position = FxOptionPosition("EURUSD", 1.10, 1.15, 0.25, 0.02, 0.01, 0.12, OptionType.CALL)

    result = price_fx_option(position)

    assert result.symbol == "EURUSD"
    assert 0.0 < result.price < 0.10
    assert 0.0 < result.delta < 1.0
    assert result.gamma > 0
    assert result.vega > 0


def test_fx_put_delta_is_negative():
    position = FxOptionPosition("USDJPY", 135.0, 130.0, 0.50, 0.015, 0.005, 0.10, OptionType.PUT)

    result = price_fx_option(position)

    assert result.price > 0
    assert result.delta < 0

