# Market Risk Platform

Market-risk service with local risk calculations, API access, infrastructure code, and deployment controls.

The repository is organized around a small risk workload and the surrounding platform pieces needed to build, test, deploy, and operate it. The application exposes FX option risk and portfolio-risk calculations through both a CLI and FastAPI service. The infrastructure and CI files show how the service would be packaged, validated, and promoted through controlled environments.

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

## Run Locally

The API can be run locally without AWS credentials.

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

The production environment includes an S3/DynamoDB remote-state pattern with placeholder names. Replace those before using it in a real AWS account.

## Financial-Services Context

Market-risk workloads require reproducible calculations, controlled releases, auditable infrastructure changes, and clear operational visibility. This project focuses on those platform concerns around a small pricing and portfolio-risk service.
