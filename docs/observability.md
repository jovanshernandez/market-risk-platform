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

The API emits metrics with `prometheus_client` from:

```text
app/market_risk_platform/metrics.py
```

Request metrics are labeled by route template (`/risk/portfolio`), not the raw URL, and requests that match no route are labeled `unmatched`, so label cardinality stays bounded. Risk gauges are recomputed from the sample book on every scrape.

## API Metrics

| Metric | Type | Labels | Source |
| --- | --- | --- | --- |
| `market_risk_platform_up` | gauge | none | Static API health indicator emitted by `/metrics`. |
| `market_risk_http_requests_total` | counter | `method`, `path`, `status` | FastAPI middleware counts requests after each response. |
| `market_risk_http_request_duration_seconds` | histogram | `method`, `path` | Request latency, for p95 latency SLOs. |
| `market_risk_portfolio_beta` | gauge | `symbol` | Beta of each sample holding against SPY. |
| `market_risk_portfolio_sharpe` | gauge | none | Annualized Sharpe from the sample portfolio return series. |
| `market_risk_portfolio_var_95_10d` | gauge | none | 10-day 95% VaR from the Monte Carlo portfolio run. |
| `market_risk_portfolio_expected_shortfall_95_10d` | gauge | none | Expected shortfall from the same Monte Carlo run. |
| `market_risk_portfolio_mean_pnl` | gauge | none | Mean simulated PnL from the Monte Carlo run. |
| `market_risk_fx_option_price` | gauge | `symbol` | Garman-Kohlhagen model price for each sample FX option. |
| `market_risk_fx_option_delta` | gauge | `symbol` | Delta for each sample FX option. |
| `market_risk_fx_option_vega` | gauge | `symbol` | Vega per 1 vol point for each sample FX option. |
| `market_risk_fx_option_notional_value` | gauge | `symbol`, `currency` | Model price multiplied by notional, in the pair's quote currency. |
| `market_risk_last_success_timestamp_seconds` | gauge | none | Unix time of the last successful risk calculation; drives the freshness panel. |
| `market_risk_calculation_failures_total` | counter | none | Risk calculations that raised during a scrape. |

## Dashboard Panels

| Panel | Query | Meaning |
| --- | --- | --- |
| API Availability | `up{job="market-risk-api"}` | Shows whether Prometheus can scrape the API. A value of `1` means the target is up. |
| Annualized Sharpe | `market_risk_portfolio_sharpe` | Displays the sample portfolio's annualized risk-adjusted return metric. |
| 10D 95% VaR | `market_risk_portfolio_var_95_10d` | Shows the simulated 10-day 95% value at risk. |
| Expected Shortfall | `market_risk_portfolio_expected_shortfall_95_10d` | Shows the average simulated loss beyond the VaR threshold. |
| Request Rate by Path | `sum by (path) (rate(market_risk_http_requests_total[5m]))` | Shows API request throughput grouped by route. |
| Portfolio Beta | `market_risk_portfolio_beta` | Compares sample beta values for AAPL, MSFT, and XLK. |
| FX Option Notional Value | `market_risk_fx_option_notional_value` | Shows modeled value by FX option symbol, labeled with its currency (USDJPY is in JPY). |
| FX Option Delta | `market_risk_fx_option_delta` | Shows directional exposure by FX option symbol. |
| FX Option Vega | `market_risk_fx_option_vega` | Shows volatility exposure by FX option symbol. |
| FX Option Price | `market_risk_fx_option_price` | Shows model price by FX option symbol. |
| Risk Data Freshness | `time() - market_risk_last_success_timestamp_seconds` | Shows seconds since the latest successful sample risk calculation. |
| p95 Latency by Path | `histogram_quantile(0.95, sum by (le, path) (rate(market_risk_http_request_duration_seconds_bucket[5m])))` | 95th percentile request latency per route. |
| 5xx Error Ratio | `sum(rate(market_risk_http_requests_total{status=~"5.."}[5m])) / sum(rate(market_risk_http_requests_total[5m]))` | Share of requests failing server-side. |

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
time() - market_risk_last_success_timestamp_seconds
```

## Generating Traffic

The request-rate panel needs traffic before it becomes visually useful:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/risk/fx-options
curl http://127.0.0.1:8000/risk/portfolio
```

The risk metrics are emitted directly from the API's deterministic sample workload, so they are available as soon as Prometheus scrapes `/metrics`.

## Running Without Docker

`docker compose up --build` is the simplest way to run the API, Prometheus and Grafana together. Where Docker isn't available, the native macOS configs point Prometheus at `127.0.0.1:8000` instead of the compose service name.

```bash
brew install prometheus grafana
```

Start the API (from `app/`, with the repo venv active):

```bash
uvicorn market_risk_platform.api:app --host 127.0.0.1 --port 8000
```

Start Prometheus from the repo root:

```bash
prometheus \
  --config.file=observability/prometheus/prometheus.local.yml \
  --storage.tsdb.path=/tmp/market-risk-prometheus-data \
  --web.listen-address=127.0.0.1:9090
```

Start Grafana from the repo root:

```bash
grafana server \
  --config /opt/homebrew/etc/grafana/grafana.ini \
  --homepath /opt/homebrew/opt/grafana/share/grafana \
  cfg:default.paths.provisioning=$(pwd)/observability/grafana/provisioning-local \
  cfg:default.paths.data=/tmp/market-risk-grafana-data \
  cfg:default.paths.logs=/tmp/market-risk-grafana-logs \
  cfg:server.http_addr=127.0.0.1 \
  cfg:server.http_port=3000 \
  cfg:security.admin_user=admin \
  cfg:security.admin_password=admin
```
