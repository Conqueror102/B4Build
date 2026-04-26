output "ecr_repository_url" {
  description = "ECR image URL (registry/repo), tag with :latest or :sha in CI"
  value       = aws_ecr_repository.backend.repository_url
}

output "ecr_repository_arn" {
  value = aws_ecr_repository.backend.arn
}

output "ecr_repository_name" {
  value = aws_ecr_repository.backend.name
}

output "github_actions_role_arn" {
  description = "Set GitHub secret AWS_ROLE_ARN to this value. After setting cicd_terraform_state_s3_bucket and apply, the role can run Terraform in envs/dev from GitHub. Also set repository variable CICD_TERRAFORM_STATE_S3_BUCKET (same as bucket) for deploy-backend."
  value       = aws_iam_role.github_actions_deploy.arn
}

output "oidc_provider_arn" {
  value = aws_iam_openid_connect_provider.github.arn
}
