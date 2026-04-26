terraform {
  required_version = ">= 1.6"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Update bucket name after creating S3 bucket (see README.md)
  backend "s3" {
    bucket         = "YOUR_BUCKET_NAME_HERE"
    key            = "shared/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "b4build-terraform-lock"
    encrypt        = true
  }
}

provider "aws" {
  region = "us-east-1"

  default_tags {
    tags = {
      Project     = "b4build"
      Environment = "shared"
      ManagedBy   = "terraform"
    }
  }
}
