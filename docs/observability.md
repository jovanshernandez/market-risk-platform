# Observability

The local observability stack is built around three services:

- **Market Risk API** exposes HTTP endpoints and Prometheus metrics.
- **Prometheus** scrapes the API's `/metrics` endpoint.
- **Grafana** reads from Prometheus and renders the `Market Risk Platform Overview` dashboard.

## Metrics Flow

```text
FastAPI service
  -> /metrics
  -> Prometheus scrape job: market-risk-api
  -> Grafana datasource: Prometheus
  -> Market Risk Platform Overview dashboard
```

Prometheus is configured in:

```text
observability/prometheus/prometheus.yml
```

Grafana datasource and dashboard provisioning are configured in:

```text
observability/grafana/provisioning/
observability/grafana/dashboards/market-risk-overview.json
```

The API emits metrics from:

```text
app/market_risk_platform/api.py
```

## API Metrics

| Metric | Type | Labels | Source |
| --- | --- | --- | --- |
| `market_risk_platform_up` | gauge | none | Static API health indicator emitted by `/metrics`. |
| `market_risk_http_requests_total` | counter | `method`, `path`, `status` | FastAPI middleware counts requests after each response. |
| `market_risk_portfolio_beta` | gauge | `symbol` | Portfolio beta values from `build_portfolio_risk()`. |
| `market_risk_portfolio_sharpe` | gauge | none | Annualized Sharpe from the sample portfolio return series. |
| `market_risk_portfolio_var_95_10d` | gauge | none | 10-day 95% VaR from the Monte Carlo portfolio run. |
| `market_risk_portfolio_expected_shortfall_95_10d` | gauge | none | Expected shortfall from the same Monte Carlo run. |
| `market_risk_portfolio_mean_pnl` | gauge | none | Mean simulated PnL from the Monte Carlo run. |
| `market_risk_fx_option_price` | gauge | `symbol` | Garman-Kohlhagen model price for each sample FX option. |
| `market_risk_fx_option_delta` | gauge | `symbol` | Delta for each sample FX option. |
| `market_risk_fx_option_vega` | gauge | `symbol` | Vega for each sample FX option. |
| `market_risk_fx_option_notional_value` | gauge | `symbol` | Model price multiplied by notional for each sample FX option. |
| `quant_risk_last_success_timestamp_seconds` | gauge | none | Timestamp used to measure risk data freshness. |

## Dashboard Panels

| Panel | Query | Meaning |
| --- | --- | --- |
| API Availability | `up{job="market-risk-api"}` | Shows whether Prometheus can scrape the API. A value of `1` means the target is up. |
| Annualized Sharpe | `market_risk_portfolio_sharpe` | Displays the sample portfolio's annualized risk-adjusted return metric. |
| 10D 95% VaR | `market_risk_portfolio_var_95_10d` | Shows the simulated 10-day 95% value at risk. |
| Expected Shortfall | `market_risk_portfolio_expected_shortfall_95_10d` | Shows the average simulated loss beyond the VaR threshold. |
| Request Rate by Path | `sum by (path) (rate(market_risk_http_requests_total[5m]))` | Shows API request throughput grouped by route. |
| Portfolio Beta | `market_risk_portfolio_beta` | Compares sample beta values for AAPL, MSFT, and XLK. |
| FX Option Notional Value | `market_risk_fx_option_notional_value` | Shows modeled notional value by FX option symbol. |
| FX Option Delta | `market_risk_fx_option_delta` | Shows directional exposure by FX option symbol. |
| FX Option Vega | `market_risk_fx_option_vega` | Shows volatility exposure by FX option symbol. |
| FX Option Price | `market_risk_fx_option_price` | Shows model price by FX option symbol. |
| Risk Data Freshness | `time() - quant_risk_last_success_timestamp_seconds` | Shows seconds since the latest successful sample risk calculation. |

## Prometheus Queries

Use the Prometheus expression browser at:

```text
http://127.0.0.1:9090
```

Useful queries:

```promql
up{job="market-risk-api"}
```

```promql
sum by (path) (rate(market_risk_http_requests_total[5m]))
```

```promql
market_risk_portfolio_beta
```

```promql
market_risk_portfolio_var_95_10d
```

```promql
market_risk_fx_option_notional_value
```

```promql
time() - quant_risk_last_success_timestamp_seconds
```

## Generating Traffic

The request-rate panel needs traffic before it becomes visually useful:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/risk/fx-options
curl http://127.0.0.1:8000/risk/portfolio
```

The risk metrics are emitted directly from the API's deterministic sample workload, so they are available as soon as Prometheus scrapes `/metrics`.
