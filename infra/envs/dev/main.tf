data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

# Resolve ECR from shared (same account; set ecr_repository_name to match)
data "aws_ecr_repository" "backend" {
  name = var.ecr_repository_name
}

locals {
  name_prefix  = "${var.project_name}-${var.environment}"
  account_id   = data.aws_caller_identity.current.account_id
  cluster_name = local.name_prefix
  service_name = "${var.project_name}-backend"
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
