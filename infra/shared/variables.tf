variable "aws_region" {
  description = "Region for shared resources (ECR, OIDC, CI/CD role)"
  type        = string
  default     = "us-east-1"
}

variable "github_org" {
  description = "GitHub org or user for trust policy (e.g. myuser)"
  type        = string
  default     = "YOUR_GITHUB_ORG"
}

variable "github_repo" {
  description = "Repository name in github_org/repo (e.g. ai-build-advisor)"
  type        = string
  default     = "YOUR_GITHUB_REPO"
}

variable "ecr_repo_name" {
  description = "ECR repository name (must match deploy-backend.yml ECR_REPOSITORY)"
  type        = string
  default     = "b4build/backend"
}

# Set to the same S3 bucket name you use in infra/envs/dev/backend.tf so GitHub Actions can run
# `terraform init` and pin ECS to ECR:git_sha. Optional extra: attach AdministratorAccess in dev.
variable "cicd_terraform_state_s3_bucket" {
  description = "S3 state bucket (same as envs/dev backend 'bucket' value). Empty = do not expand GitHub role for Terraform/CI image pins."
  type        = string
  default     = ""
}

variable "cicd_terraform_dynamodb_table" {
  description = "DynamoDB state lock table name; must match backend 'dynamodb_table' in envs/dev and shared."
  type        = string
  default     = "b4build-terraform-lock"
}

# When true (default) and state bucket is set, attach arn:aws:iam::aws:policy/AdministratorAccess to the GitHub OIDC role. Dev-only; never use a prod account.
variable "cicd_attach_terraform_admin_policy" {
  type        = bool
  default     = true
  description = "If true with non-empty state bucket, attach AWS AdministratorAccess for GitHub Actions. Set false to only grant state + targeted ECS in cicd_terraform_state_min (full terraform apply in CI may still fail for IAM, etc.)."
}
