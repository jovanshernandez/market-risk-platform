import json

import pytest

from market_risk_platform.cli import main


def test_fx_options_table(capsys):
    assert main(["fx-options"]) == 0
    out = capsys.readouterr().out
    assert "EURUSD" in out and "USDJPY" in out and "GBPUSD" in out


def test_portfolio_json(capsys):
    assert main(["portfolio", "--json", "--confidence", "0.99", "--simulations", "1000"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["benchmark"] == "SPY"
    assert payload["var"]["confidence"] == 0.99
    assert payload["var"]["simulations"] == 1000


def test_portfolio_rejects_invalid_options(capsys):
    with pytest.raises(SystemExit) as exit_info:
        main(["portfolio", "--simulations", "5"])
    assert exit_info.value.code == 2
    assert "simulations" in capsys.readouterr().err
