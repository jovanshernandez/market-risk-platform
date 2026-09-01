from fastapi.testclient import TestClient

from market_risk_platform.api import app


client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_ready_endpoint_runs_dependency_checks() -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ready"
    assert payload["checks"]["portfolio_risk"] is True
    assert payload["checks"]["fx_option_risk"] is True


def test_metrics_endpoint_exposes_operational_signals() -> None:
    response = client.get("/metrics")

    assert response.status_code == 200
    body = response.text
    assert "market_risk_platform_up 1" in body
    assert "market_risk_portfolio_var_95_10d" in body
    assert "market_risk_fx_option_price" in body
