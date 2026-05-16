output "api_instance_id" {
  description = "EC2 instance ID for the API host."
  value       = aws_instance.api.id
}

output "api_public_ip" {
  description = "Public IP for the API host."
  value       = aws_instance.api.public_ip
}

output "api_url" {
  description = "HTTP URL for the market-risk API."
  value       = "http://${aws_instance.api.public_ip}:8000"
}

output "security_group_id" {
  description = "API security group ID."
  value       = aws_security_group.api.id
}

