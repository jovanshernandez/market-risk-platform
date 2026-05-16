variable "project" {
  description = "Project name used for tags and resource naming."
  type        = string
}

variable "environment" {
  description = "Deployment environment."
  type        = string
}

variable "aws_region" {
  description = "AWS region for deployment."
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the service VPC."
  type        = string
}

variable "public_subnet_cidr" {
  description = "CIDR block for the public subnet."
  type        = string
}

variable "instance_type" {
  description = "EC2 instance type for the API host."
  type        = string
  default     = "t3.micro"

  validation {
    condition     = contains(["t3.micro", "t3.small", "t3.medium"], var.instance_type)
    error_message = "Use t3.micro, t3.small, or t3.medium."
  }
}

variable "ami_id" {
  description = "AMI ID for the API host."
  type        = string
}

variable "ssh_cidr_blocks" {
  description = "CIDR blocks allowed to reach SSH."
  type        = list(string)
  default     = []
}

variable "http_cidr_blocks" {
  description = "CIDR blocks allowed to reach the API."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}

variable "tags" {
  description = "Additional tags."
  type        = map(string)
  default     = {}
}
