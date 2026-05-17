# Market Risk Platform

Market-risk service with local risk calculations, API access, infrastructure code, and deployment controls.

The repository is organized around a small risk workload and the surrounding platform pieces needed to build, test, deploy, and operate it. The application exposes FX option risk and portfolio-risk calculations through both a CLI and FastAPI service. Docker Compose provides the local runtime; Terraform and Jenkins document how the service would move through infrastructure provisioning and controlled delivery.

## Project Scope

- Python package for pricing and portfolio-risk calculations
- FastAPI endpoints for health, metrics, FX option risk, and portfolio risk
- CLI entry points for running the same workloads locally
- Unit tests covering the pricing and portfolio modules
- Dockerfile for packaging the API service
- Terraform module with separate dev and prod environment definitions
- Jenkins pipeline for application tests, image build, Terraform validation, and plan capture
- Prometheus and Grafana configuration for basic service visibility
- Operational notes for architecture, security, runbooks, SLOs, and tradeoffs

## Architecture

```text
Developer / CI
  -> pytest
  -> Docker build
  -> Terraform fmt / validate / plan
  -> manual production approval
  -> AWS service environment
       -> VPC / subnet / route table
       -> EC2 API host
       -> FastAPI market-risk service
       -> Prometheus scrape target
```

## Repository Layout

```text
app/
  market_risk_platform/       Python package for pricing, portfolio risk, API, and CLI
  tests/                Unit tests for pricing and risk logic
  Dockerfile
ci/
  Jenkinsfile           CI/CD pipeline
infra/
  terraform/
    modules/service/    Reusable AWS service module
    environments/dev/   Local/backendless validation target
    environments/prod/  Remote-state production pattern
observability/
  prometheus/
  grafana/
docs/
  architecture.md
  runbook.md
  security.md
  tradeoffs.md
```

## Recommended Local Run

Docker Compose is the recommended local workflow. It starts the API, Prometheus, and Grafana with the same service wiring used by the repository's observability configuration.

Prerequisites:

- Docker Desktop, or
- Docker CLI with Colima on macOS:

```bash
brew install docker docker-compose colima
colima start --cpu 2 --memory 4 --disk 20
```

Start the stack:

```bash
docker compose up --build
```

Open:

- API docs: `http://127.0.0.1:8000/docs`
- Prometheus: `http://127.0.0.1:9090`
- Grafana: `http://127.0.0.1:3000`
- Grafana dashboard: `http://127.0.0.1:3000/d/market-risk-overview/market-risk-platform-overview`

Grafana credentials:

```text
username: admin
password: admin
```

Generate API traffic before checking request-rate panels:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/risk/fx-options
curl http://127.0.0.1:8000/risk/portfolio
```

Stop the stack:

```bash
docker compose down
```

## API Development

Run the Python service directly when working on application code or tests without the observability stack.

### 1. Create a virtual environment

```bash
cd app
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run tests

```bash
pytest -q
```

Expected result:

```text
5 passed
```

### 4. Run the CLI workloads

```bash
python -m market_risk_platform.cli fx-options
python -m market_risk_platform.cli portfolio
```

### 5. Start only the FastAPI server

```bash
uvicorn market_risk_platform.api:app --reload --host 127.0.0.1 --port 8000
```

Open the interactive API docs:

```text
http://127.0.0.1:8000/docs
```

Useful endpoints:

- `GET /health`
- `GET /metrics`
- `GET /risk/fx-options`
- `GET /risk/portfolio`

Stop the server with `Ctrl+C`.

## Native Observability Fallback

The native macOS configs are included for environments where Docker is unavailable. Docker Compose should be used when possible.

```bash
brew install prometheus grafana
```

Start the API:

```bash
cd app
source .venv/bin/activate
python -m uvicorn market_risk_platform.api:app --host 127.0.0.1 --port 8000
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

## Observability

The local observability stack has three services:

- **Market Risk API** runs the FastAPI service and exposes risk endpoints plus Prometheus metrics on `/metrics`.
- **Prometheus** scrapes the API metrics endpoint and stores time-series data locally.
- **Grafana** uses Prometheus as a datasource and renders the `Market Risk Platform Overview` dashboard.

### Service URLs

```text
Market Risk API docs: http://127.0.0.1:8000/docs
Prometheus:           http://127.0.0.1:9090
Grafana:              http://127.0.0.1:3000
Grafana dashboard:    http://127.0.0.1:3000/d/market-risk-overview/market-risk-platform-overview
```

Grafana login:

```text
admin / admin
```

### Metrics Exposed By The API

The API exports these Prometheus metrics:

- `market_risk_platform_up`: service health gauge.
- `market_risk_http_requests_total`: request counter labeled by method, path, and status.
- `market_risk_portfolio_beta`: beta by portfolio symbol.
- `market_risk_portfolio_sharpe`: annualized Sharpe ratio.
- `market_risk_portfolio_var_95_10d`: simulated 10-day 95% value at risk.
- `market_risk_portfolio_expected_shortfall_95_10d`: simulated 10-day expected shortfall.
- `market_risk_portfolio_mean_pnl`: simulated mean PnL.
- `market_risk_fx_option_price`: FX option model price by symbol.
- `market_risk_fx_option_delta`: FX option delta by symbol.
- `market_risk_fx_option_vega`: FX option vega by symbol.
- `market_risk_fx_option_notional_value`: notional model value by symbol.
- `quant_risk_last_success_timestamp_seconds`: timestamp of the latest successful sample risk calculation.

### Dashboard Panels

The Grafana dashboard includes:

- **API Availability**: whether Prometheus can scrape the API.
- **Annualized Sharpe**: portfolio risk-adjusted return metric from the sample return series.
- **10D 95% VaR**: estimated portfolio loss threshold over a 10-day horizon at 95% confidence.
- **Expected Shortfall**: average loss beyond the VaR threshold.
- **Request Rate by Path**: request throughput grouped by API route.
- **Portfolio Beta**: beta values for AAPL, MSFT, and XLK against the benchmark series.
- **FX Option Notional Value**: modeled notional value for the sample EURUSD, USDJPY, and GBPUSD positions.
- **FX Option Delta**: directional exposure by FX option.
- **FX Option Vega**: volatility exposure by FX option.
- **FX Option Price**: model price by FX option.
- **Risk Data Freshness**: seconds since the latest successful sample risk calculation.

### Useful Prometheus Queries

Use the Prometheus expression browser at `http://127.0.0.1:9090`:

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

Generate API traffic before viewing request-rate graphs:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/risk/fx-options
curl http://127.0.0.1:8000/risk/portfolio
```

## Deployment And Change Control

Terraform and Jenkins are included to show the path from a local service to a managed environment. They are not required to run the local Docker Compose stack.

- **Terraform** defines the AWS-facing infrastructure boundary: VPC, subnet, route table, security group, and API host. The repo keeps separate `dev` and `prod` environment definitions so infrastructure changes can be reviewed before promotion.
- **Jenkins** models the CI/CD control plane: run application tests, build the container image, validate Terraform, capture a plan artifact, and require approval before production changes.
- **Docker Compose** remains the recommended local workflow. Terraform and Jenkins represent the deployment and change-management layer around the same service.

This separation keeps local development fast while preserving the release controls expected for risk and market-data workloads.

## Terraform Validation

```bash
cd infra/terraform/environments/dev
terraform init -backend=false
terraform validate
terraform plan -var='ami_id=ami-0123456789abcdef0'
```

The production environment includes an S3/DynamoDB remote-state pattern with placeholder names. Replace those before using it in a real AWS account.
