# SRE Notes

## Suggested SLOs

- API availability: 99.9% monthly for `/health`.
- Readiness: `/ready` succeeds before traffic is routed to a freshly deployed service.
- Risk freshness: sample risk output updated within expected job interval.
- API latency: 95% of risk API requests complete within 500 ms for cached/sample workloads, measured from `market_risk_http_request_duration_seconds`.

## Alerts

- API down for more than 2 minutes.
- Readiness check fails after deployment.
- Risk freshness exceeds threshold.
- Error rate exceeds 5% over 5 minutes.
- Terraform apply fails after approval.

## Operational Signals

- Deployment frequency and rollback rate.
- Terraform plan drift and resource replacement count.
- Last successful risk run timestamp.
- API request volume, latency, and error rate.
- Health and readiness check results.
