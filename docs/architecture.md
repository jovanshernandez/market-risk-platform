# Architecture

## System Goal

Provide a deployable service for market-risk workloads. The service calculates sample FX option Greeks and portfolio risk statistics, then exposes the results through an HTTP API and CLI.

## Components

- **Risk API**: FastAPI service with health, metrics, FX option risk, and portfolio risk endpoints.
- **Risk Library**: Pure Python pricing and portfolio modules that can be tested independently from the web layer.
- **Container**: Docker image for repeatable runtime packaging.
- **Terraform**: AWS VPC, public subnet, route table, security group, and EC2 API host.
- **CI/CD**: Jenkins pipeline that runs tests, builds the image, validates infrastructure, archives a plan, and gates production changes.
- **Observability**: Prometheus scrape config and Grafana dashboard starter.

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
