# Tradeoffs

## EC2 Instead Of ECS/EKS

The Terraform module uses a single EC2 host to keep the infrastructure easy to inspect. In production, ECS or EKS would be better for rolling deploys, image provenance, service discovery, autoscaling, and runtime isolation.

## Deterministic Sample Data

The project avoids live market-data dependencies by default so tests are repeatable. A production version would separate provider adapters, data validation, and cache/storage concerns.

## Jenkins

Jenkins is included because many financial-services firms still operate Jenkins at scale. The same workflow can be translated to GitHub Actions, GitLab CI, or Buildkite.

## Normal Monte Carlo VaR

VaR and expected shortfall come from a Monte Carlo simulation that draws normal daily returns with the portfolio's sample mean and volatility. That is fast and easy to reason about, but it understates fat tails. Historical simulation or a filtered (GARCH) model would be the next step for a real book.

## Prometheus Gauges Recomputed On Scrape

The sample book is cheap to price (a few milliseconds), so `/metrics` recomputes it on every scrape. A real system would run risk on a schedule, cache the result, and have `/metrics` only read it, so a slow calculation can't stall the scrape.
