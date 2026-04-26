# Remote state: S3 + DynamoDB lock (see docs/SETUP_GUIDE.md)
terraform {
  backend "s3" {
    bucket         = "terraforms-state-301276847006-us-east-1-an"
    key            = "envs/dev/terraform.tfstate"
    region         = "us-east-1"
    dynamodb_table = "b4build-terraform-lock"
    encrypt        = true
  }
}
