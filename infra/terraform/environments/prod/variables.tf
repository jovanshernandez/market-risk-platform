variable "aws_region" {
  description = "AWS region for prod."
  type        = string
  default     = "us-west-2"
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
  default     = []
}

