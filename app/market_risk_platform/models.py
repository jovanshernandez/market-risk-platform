"""Domain objects shared by the pricing and portfolio modules."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class OptionType(str, Enum):
    CALL = "call"
    PUT = "put"


@dataclass(frozen=True)
class FxOptionPosition:
    """A European FX option on a currency pair quoted as BASEQUOTE (e.g. EURUSD).

    The base currency is the "foreign" currency and the quote currency is the
    "domestic" currency in Garman-Kohlhagen terms. ``notional`` is in base
    currency units.
    """

    symbol: str
    spot: float
    strike: float
    maturity_years: float
    domestic_rate: float
    foreign_rate: float
    volatility: float
    option_type: OptionType
    notional: float = 1_000_000.0

    @property
    def premium_currency(self) -> str:
        """Currency the model price is expressed in (the quote currency)."""
        return self.symbol[3:] if len(self.symbol) == 6 else ""


@dataclass(frozen=True)
class RiskResult:
    """Model price and Greeks for one FX option, per unit of base-currency notional.

    - ``price``: premium in quote currency per 1 unit of base currency.
    - ``delta``: spot delta (premium-unadjusted).
    - ``gamma``: change in delta per 1.00 move in spot.
    - ``vega``: change in price for a 1 vol point (0.01) move in volatility.
    - ``theta``: change in price per calendar day of time decay.
    - ``notional_value``: ``price * notional``, in quote currency.
    """

    symbol: str
    option_type: OptionType
    premium_currency: str
    price: float
    delta: float
    gamma: float
    vega: float
    theta: float
    notional_value: float
