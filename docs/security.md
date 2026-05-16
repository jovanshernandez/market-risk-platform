# Security Notes

- EC2 metadata requires IMDSv2.
- EBS root volumes are encrypted.
- SSH ingress is disabled by default unless CIDR blocks are explicitly supplied.
- Production Terraform uses a remote-state pattern with encryption and DynamoDB locking.
- Secrets are not stored in the repository.
- The API currently exposes sample deterministic risk data only.

## Financial-Services Controls To Add Next

- ECR image scanning and signed container images.
- Least-privilege IAM role for runtime access.
- Private subnets with ALB ingress instead of direct public instance exposure.
- WAF and rate limiting for public endpoints.
- Structured audit logs for risk runs and infrastructure changes.
- Policy-as-code gates in CI.

