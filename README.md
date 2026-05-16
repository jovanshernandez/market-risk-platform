# Market Risk Platform

Production-style platform for running market-data and portfolio-risk workloads.

This project combines quant-adjacent application logic with the platform engineering controls expected in a financial-services environment: tested Python services, containerized delivery, Terraform-managed infrastructure, Jenkins CI/CD, observability artifacts, and operational documentation.

## What This Demonstrates

- FX option pricing with Garman-Kohlhagen Greeks
- Portfolio beta, annualized Sharpe, and Monte Carlo VaR
- FastAPI service exposing risk workloads and health checks
- Docker image build for repeatable deployment
- Terraform module with separate dev and prod environments
- Jenkins pipeline for tests, image build, Terraform validation, plan artifact capture, and gated production change flow
- Prometheus/Grafana starter observability assets
- SRE docs covering architecture, runbooks, security, and tradeoffs

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
  Jenkinsfile           Portfolio-friendly CI/CD pipeline
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

## Run Locally

The app is intentionally easy to run on a laptop so reviewers can see the working API without needing AWS credentials.

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

### 5. Start the FastAPI server

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

## Local Workflow Summary

```bash
cd app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest -q
uvicorn market_risk_platform.api:app --reload --host 127.0.0.1 --port 8000
```

## Terraform Validation

```bash
cd infra/terraform/environments/dev
terraform init -backend=false
terraform validate
terraform plan -var='ami_id=ami-0123456789abcdef0'
```

The production environment includes an S3/DynamoDB remote-state pattern with placeholder names. Replace those before using it outside portfolio review.

## Why This Is Financial-Services Relevant

Financial firms care less about toy infrastructure and more about whether engineering work is reproducible, controlled, observable, and auditable. This project frames platform engineering around a realistic workload: market-risk calculations that need reliable delivery, change control, operational visibility, and clear failure handling.

The quant math is intentionally approachable. The senior signal is the system around it: CI gates, infrastructure boundaries, documented risk controls, and operations-ready defaults.
