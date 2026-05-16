import argparse
import json

from market_risk_platform.portfolio import annualized_sharpe, calculate_beta, monte_carlo_var
from market_risk_platform.pricing import price_fx_option
from market_risk_platform.sample_data import ASSET_RETURNS, FX_POSITIONS, SPY_RETURNS


def build_portfolio_risk() -> dict[str, object]:
    betas = {
        series.symbol: round(calculate_beta(series.daily_returns, SPY_RETURNS), 4)
        for series in ASSET_RETURNS
    }
    portfolio_returns = [
        sum(series.daily_returns[index] for series in ASSET_RETURNS) / len(ASSET_RETURNS)
        for index in range(len(SPY_RETURNS))
    ]
    return {
        "benchmark": "SPY",
        "betas": betas,
        "sharpe": round(annualized_sharpe(portfolio_returns), 4),
        "var_95_10d": monte_carlo_var(1_000_000, portfolio_returns, simulations=2_000),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run sample market-risk workloads.")
    parser.add_argument("workload", choices=["fx-options", "portfolio"], help="Risk workload to run")
    args = parser.parse_args()

    if args.workload == "fx-options":
        payload = [price_fx_option(position).__dict__ for position in FX_POSITIONS]
    else:
        payload = build_portfolio_risk()

    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
