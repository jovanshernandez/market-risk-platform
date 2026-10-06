# Tests against a mocked AWS provider: no credentials and no AWS API calls.
# "apply" here only runs against the mock, so computed attributes get fake values.
# Run from infra/terraform/modules/service with `terraform init && terraform test`.

mock_provider "aws" {}

variables {
  project            = "market-risk-platform"
  environment        = "test"
  vpc_cidr           = "10.60.0.0/16"
  public_subnet_cidr = "10.60.1.0/24"
  ami_id             = "ami-0123456789abcdef0"
  container_image    = "example.dkr.ecr.us-east-1.amazonaws.com/market-risk-platform:abc1234"
}

run "secure_defaults" {
  command = apply

  assert {
    condition     = aws_instance.api.metadata_options[0].http_tokens == "required"
    error_message = "IMDSv2 must be required on the API host."
  }

  assert {
    condition     = aws_instance.api.root_block_device[0].encrypted
    error_message = "The root volume must be encrypted."
  }

  assert {
    condition     = length(aws_security_group.api.ingress) == 0
    error_message = "With no CIDR blocks supplied, the security group must allow no ingress."
  }

  assert {
    condition     = aws_instance.api.instance_type == "t3.micro"
    error_message = "Default instance type should be t3.micro."
  }
}

run "tags_and_naming" {
  command = apply

  variables {
    tags = { CostCenter = "risk" }
  }

  assert {
    condition     = aws_vpc.this.tags["Name"] == "market-risk-platform-test-vpc"
    error_message = "Resources should be named <project>-<environment>-<role>."
  }

  assert {
    condition = alltrue([
      aws_instance.api.tags["Environment"] == "test",
      aws_instance.api.tags["ManagedBy"] == "terraform",
      aws_instance.api.tags["CostCenter"] == "risk",
    ])
    error_message = "Standard and caller-supplied tags must be merged onto resources."
  }
}

run "runs_the_pinned_image" {
  command = apply

  assert {
    condition     = strcontains(aws_instance.api.user_data, "market-risk-platform:abc1234")
    error_message = "User data must run the container_image passed in."
  }
}

run "opens_only_requested_ingress" {
  command = apply

  variables {
    http_cidr_blocks = ["203.0.113.0/24"]
    ssh_cidr_blocks  = ["198.51.100.10/32"]
  }

  assert {
    condition     = length(aws_security_group.api.ingress) == 2
    error_message = "Expected one API rule and one SSH rule."
  }

  assert {
    condition = alltrue([
      for rule in aws_security_group.api.ingress :
      !contains(rule.cidr_blocks, "0.0.0.0/0")
    ])
    error_message = "Ingress must be limited to the CIDR blocks supplied."
  }
}

run "rejects_unapproved_instance_type" {
  command = plan

  variables {
    instance_type = "m5.24xlarge"
  }

  expect_failures = [var.instance_type]
}

run "rejects_malformed_inputs" {
  command = plan

  variables {
    ami_id   = "not-an-ami"
    vpc_cidr = "10.60.0.0/99"
  }

  expect_failures = [var.ami_id, var.vpc_cidr]
}
