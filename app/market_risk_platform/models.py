from dataclasses import dataclass
from enum import Enum


class OptionType(str, Enum):
    CALL = "call"
    PUT = "put"


@dataclass(frozen=True)
class FxOptionPosition:
    symbol: str
    spot: float
    strike: float
    maturity_years: float
    domestic_rate: float
    foreign_rate: float
    volatility: float
    option_type: OptionType
    notional: float = 1_000_000.0


@dataclass(frozen=True)
class RiskResult:
    symbol: str
    price: float
    delta: float
    gamma: float
    vega: float
    theta: float
    notional_value: float

