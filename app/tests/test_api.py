import pytest
from fastapi.testclient import TestClient

from market_risk_platform.api import app

client = TestClient(app)

PORTFOLIO_REQUEST = {
    "portfolio_value": 500_000,
    "benchmark_returns": [0.004, -0.002, 0.006, 0.001, -0.005, 0.003],
    "assets": [
        {"symbol": "AAPL", "weight": 0.6, "daily_returns": [0.006, -0.003, 0.009, 0.002, -0.008, 0.004]},
        {"symbol": "MSFT", "weight": 0.4, "daily_returns": [0.005, -0.002, 0.007, 0.001, -0.006, 0.004]},
    ],
    "confidence": 0.99,
    "simulations": 1000,
}


def test_health() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_runs_risk_checks() -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready", "checks": {"portfolio_risk": True, "fx_option_risk": True}}


def test_ready_returns_503_when_a_check_fails(monkeypatch) -> None:
    def broken():
        raise RuntimeError("market data unavailable")

    monkeypatch.setattr("market_risk_platform.api.sample_portfolio_risk", broken)
    response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["status"] == "not_ready"


def test_sample_fx_option_risk() -> None:
    response = client.get("/risk/fx-options")

    assert response.status_code == 200
    payload = response.json()
    assert [row["symbol"] for row in payload] == ["EURUSD", "USDJPY", "GBPUSD"]
    assert {row["premium_currency"] for row in payload} == {"USD", "JPY"}


def test_price_fx_options() -> None:
    option = {
        "symbol": "EURUSD",
        "spot": 1.10,
        "strike": 1.15,
        "maturity_years": 0.25,
        "domestic_rate": 0.02,
        "foreign_rate": 0.01,
        "volatility": 0.12,
        "option_type": "call",
    }
    response = client.post("/risk/fx-options", json=[option, option | {"option_type": "put"}])

    assert response.status_code == 200
    call, put = response.json()
    assert call["delta"] > 0 > put["delta"]
    assert call["notional_value"] == pytest.approx(call["price"] * 1_000_000, abs=1.0)


@pytest.mark.parametrize(
    "change",
    [{"symbol": "EUR/USD"}, {"spot": 0}, {"volatility": -0.1}, {"option_type": "straddle"}],
)
def test_price_fx_options_validates_input(change) -> None:
    option = {
        "symbol": "EURUSD",
        "spot": 1.10,
        "strike": 1.15,
        "maturity_years": 0.25,
        "domestic_rate": 0.02,
        "foreign_rate": 0.01,
        "volatility": 0.12,
        "option_type": "call",
    } | change

    assert client.post("/risk/fx-options", json=[option]).status_code == 422


def test_sample_portfolio_risk() -> None:
    response = client.get("/risk/portfolio")

    assert response.status_code == 200
    payload = response.json()
    assert payload["benchmark"] == "SPY"
    assert set(payload["betas"]) == {"AAPL", "MSFT", "XLK"}
    assert payload["var"]["confidence"] == 0.95
    assert payload["var"]["horizon_days"] == 10
    assert payload["var"]["expected_shortfall"] >= payload["var"]["value_at_risk"] > 0


def test_custom_portfolio_risk() -> None:
    response = client.post("/risk/portfolio", json=PORTFOLIO_REQUEST)

    assert response.status_code == 200
    payload = response.json()
    assert payload["portfolio_value"] == 500_000
    assert payload["weights"] == {"AAPL": 0.6, "MSFT": 0.4}
    assert payload["portfolio_beta"] == pytest.approx(
        0.6 * payload["betas"]["AAPL"] + 0.4 * payload["betas"]["MSFT"], abs=1e-3
    )
    assert payload["var"]["confidence"] == 0.99


@pytest.mark.parametrize(
    "change",
    [
        {"assets": [{"symbol": "AAPL", "weight": 0.5, "daily_returns": [0.01, 0.02, 0.0, 0.01, 0.0, 0.01]}]},
        {"assets": [{"symbol": "AAPL", "weight": 1.0, "daily_returns": [0.01, 0.02]}]},
        {"simulations": 100_000, "horizon_days": 250},
        {"confidence": 1.0},
    ],
)
def test_custom_portfolio_validates_input(change) -> None:
    assert client.post("/risk/portfolio", json=PORTFOLIO_REQUEST | change).status_code == 422


def test_metrics_exposes_risk_and_request_telemetry() -> None:
    client.get("/health")
    client.get("/no-such-path")
    client.get("/openapi.json")
    response = client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    body = response.text
    assert "market_risk_platform_up 1.0" in body
    assert 'market_risk_http_requests_total{method="GET",path="/health",status="200"}' in body
    assert 'market_risk_http_requests_total{method="GET",path="unmatched",status="404"}' in body
    assert 'market_risk_http_requests_total{method="GET",path="/openapi.json",status="200"}' in body
    assert "market_risk_http_request_duration_seconds_bucket" in body
    assert "market_risk_portfolio_var_95_10d " in body
    assert 'market_risk_fx_option_notional_value{currency="JPY",symbol="USDJPY"}' in body
    assert "market_risk_last_success_timestamp_seconds " in body
    assert "_created" not in body
