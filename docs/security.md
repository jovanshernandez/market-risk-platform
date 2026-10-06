# Security Notes

- EC2 metadata requires IMDSv2.
- EBS root volumes are encrypted.
- SSH and API ingress are both closed by default; each opens only to CIDR blocks passed in explicitly.
- The container runs as a non-root user.
- The host runs a pinned `container_image` (registry path plus git SHA tag) rather than `latest`.
- Production Terraform uses a remote-state pattern with encryption and DynamoDB locking.
- Secrets are not stored in the repository.
- The API currently exposes sample deterministic risk data only. Request bodies are validated by pydantic, and the Monte Carlo endpoint caps simulations x horizon so one request can't monopolize the worker.

## Financial-Services Controls To Add Next

- ECR image scanning and signed container images.
- Least-privilege IAM role for runtime access.
- Private subnets with ALB ingress instead of direct public instance exposure.
- WAF and rate limiting for public endpoints.
- Structured audit logs for risk runs and infrastructure changes.
- Policy-as-code gates in CI.

