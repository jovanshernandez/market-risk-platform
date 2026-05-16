# Runbook

## API Health Check Fails

1. Check `/health` from the host or load balancer.
2. Confirm the container is running.
3. Review application logs for import errors, dependency failures, or startup exceptions.
4. Check EC2 security group rules for port `8000`.
5. Roll back to the previous image if the failure followed a deployment.

## Risk Endpoint Returns Unexpected Results

1. Re-run unit tests for pricing and portfolio modules.
2. Check whether input assumptions changed: rates, volatilities, maturities, or return windows.
3. Compare output from the API and CLI for the same workload.
4. Capture the request, response, git SHA, and deployment timestamp for review.

## Terraform Plan Shows Risky Changes

1. Inspect replacement actions first, especially VPC, subnet, and instance recreation.
2. Confirm environment variables and workspace are correct.
3. Validate that CIDR and AMI changes were intentional.
4. Require peer approval before applying production changes.

## Market Data Provider Failure

This demo uses deterministic sample data. In a live version:

1. Alert when the last successful ingestion timestamp exceeds the freshness SLO.
2. Fail closed for trading/risk decisions that require current data.
3. Serve clearly marked stale data only for read-only dashboards.
4. Preserve the failed payload and provider response for incident review.

