terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

module "market_risk_service" {
  source = "../../modules/service"

  project            = "market-risk-platform"
  environment        = "dev"
  aws_region         = var.aws_region
  vpc_cidr           = "10.40.0.0/16"
  public_subnet_cidr = "10.40.1.0/24"
  ami_id             = var.ami_id
  instance_type      = "t3.micro"
  ssh_cidr_blocks    = var.ssh_cidr_blocks
  http_cidr_blocks   = var.http_cidr_blocks
}

