# Tradeoffs

## EC2 Instead Of ECS/EKS

The Terraform module uses a single EC2 host to keep the infrastructure easy to inspect. In production, ECS or EKS would be better for rolling deploys, image provenance, service discovery, autoscaling, and runtime isolation.

## Deterministic Sample Data

The project avoids live market-data dependencies by default so tests are repeatable. A production version would separate provider adapters, data validation, and cache/storage concerns.

## Jenkins

Jenkins is included because many financial-services firms still operate Jenkins at scale. The same workflow can be translated to GitHub Actions, GitLab CI, or Buildkite.
