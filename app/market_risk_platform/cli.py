"""Command-line entry point: run the sample risk workloads without the API."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from pydantic import ValidationError

from market_risk_platform.risk import fx_option_risk, portfolio_risk, sample_portfolio_request
from market_risk_platform.schemas import FxOptionRisk, PortfolioRisk


def render_fx_options(options: Sequence[FxOptionRisk]) -> str:
    header = f"{'symbol':<8}{'type':<6}{'ccy':<5}{'price':>11}{'delta':>10}{'gamma':>10}{'vega':>10}{'theta/day':>11}{'notional value':>17}"
    lines = ["FX option risk (Garman-Kohlhagen, vega per 1 vol point)", "", header, "-" * len(header)]
    for option in options:
        lines.append(
            f"{option.symbol:<8}{option.option_type.value:<6}{option.premium_currency:<5}"
            f"{option.price:>11.6f}{option.delta:>10.4f}{option.gamma:>10.4f}{option.vega:>10.6f}"
            f"{option.theta:>11.6f}{option.notional_value:>17,.2f}"
        )
    return "\n".join(lines)


def render_portfolio(risk: PortfolioRisk) -> str:
    var = risk.var
    level = f"{var.horizon_days}d {var.confidence:.0%}"
    lines = [
        f"Portfolio risk vs {risk.benchmark} (value {risk.portfolio_value:,.2f}, "
        f"{var.simulations:,} Monte Carlo paths)",
        "",
        f"{'symbol':<8}{'weight':>9}{'beta':>9}",
        "-" * 26,
    ]
    for symbol, weight in risk.weights.items():
        lines.append(f"{symbol:<8}{weight:>9.4f}{risk.betas[symbol]:>9.4f}")
    lines += [
        "",
        f"{'portfolio beta':<26}{risk.portfolio_beta:>14.4f}",
        f"{'annualized Sharpe':<26}{risk.sharpe:>14.4f}",
        f"{level + ' VaR':<26}{var.value_at_risk:>14,.2f}",
        f"{level + ' expected shortfall':<26}{var.expected_shortfall:>14,.2f}",
        f"{'mean simulated PnL':<26}{var.mean_pnl:>14,.2f}",
        f"{'PnL volatility':<26}{var.pnl_volatility:>14,.2f}",
    ]
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m market_risk_platform.cli",
        description="Run the sample market-risk workloads.",
    )
    parser.add_argument("workload", choices=["fx-options", "portfolio"], help="risk workload to run")
    parser.add_argument("--json", action="store_true", help="print JSON instead of a table")
    parser.add_argument("--confidence", type=float, default=0.95, help="VaR confidence level (portfolio)")
    parser.add_argument("--horizon-days", type=int, default=10, help="VaR horizon in trading days (portfolio)")
    parser.add_argument("--simulations", type=int, default=2_000, help="Monte Carlo paths (portfolio)")
    parser.add_argument("--seed", type=int, default=7, help="random seed (portfolio)")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.workload == "fx-options":
        options = fx_option_risk()
        output = (
            json.dumps([option.model_dump(mode="json") for option in options], indent=2)
            if args.json
            else render_fx_options(options)
        )
    else:
        try:
            request = sample_portfolio_request(
                confidence=args.confidence,
                horizon_days=args.horizon_days,
                simulations=args.simulations,
                seed=args.seed,
            )
        except ValidationError as error:
            parser.error("; ".join(f"{'.'.join(map(str, e['loc'])) or 'input'}: {e['msg']}" for e in error.errors()))
        risk = portfolio_risk(request)
        output = risk.model_dump_json(indent=2) if args.json else render_portfolio(risk)

    print(output)
    return 0


if __name__ == "__main__":
    sys.exit(main())
