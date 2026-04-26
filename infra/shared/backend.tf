# Remote state: S3 + DynamoDB lock (see docs/SETUP_GUIDE.md)
terraform {
  backend "s3" {
    bucket         = "terraforms-state-301276847006-us-east-1-an"
    key            = "shared/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "b4build-terraform-lock"
    encrypt        = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "b4build"
      Environment = "shared"
      ManagedBy   = "terraform"
    }
  }
}
