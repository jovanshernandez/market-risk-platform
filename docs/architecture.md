# Architecture

## System Goal

Provide a deployable service for market-risk workloads. The service calculates sample FX option Greeks and portfolio risk statistics, then exposes the results through an HTTP API and CLI.

## Components

- **Risk API**: FastAPI service with health, readiness, metrics, FX option risk, and portfolio risk endpoints. Requests and responses are pydantic models, so inputs are validated and documented in the OpenAPI schema.
- **Risk Library**: Pure Python pricing (`pricing.py`) and portfolio (`portfolio.py`) modules that can be tested independently from the web layer. `risk.py` wires them into the workloads the API and CLI share.
- **Container**: Docker image for repeatable runtime packaging.
- **Terraform**: AWS VPC, public subnet, route table, security group, and EC2 API host.
- **CI/CD**: GitHub Actions runs the Python tests and Terraform fmt / validate / test on every push. The Jenkins pipeline models the fuller delivery path: tests, image build, Terraform plan archive, and a manual production gate.
- **Observability**: Prometheus scrape config and a provisioned Grafana dashboard.

## Data Flow

```text
Sample market inputs
  -> pricing / portfolio modules
  -> FastAPI endpoints or CLI
  -> metrics and logs
  -> CI/CD and runtime validation
```

## Production Extensions

- Move market data into S3, RDS, DynamoDB, or a vendor feed cache.
- Publish Docker images to ECR instead of using a local tag.
- Run the API on ECS, EKS, or an autoscaling group behind an ALB.
- Add OpenTelemetry traces and structured JSON logs.
- Add policy-as-code checks with Checkov, tfsec, or OPA.
