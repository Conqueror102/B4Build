# GitHub Actions (OIDC role) — extend permissions when CI runs Terraform against envs/dev
# and deploy-backend pins ECS task image tags (immutable git SHA) via `terraform apply`.
#
# Set `cicd_terraform_state_s3_bucket` to the SAME S3 bucket name you use in envs/dev/backend.tf.
# With `cicd_attach_terraform_admin_policy` = true, attach Amazon AdministratorAccess in this account
# so "terraform" and "deploy-backend" GitHub jobs can read/write the full dev stack. Use a dedicated
# throwaway dev account. For least privilege, set admin = false and run Terraform for envs/dev locally.

locals {
  cicd_terraform_state_enabled = var.cicd_terraform_state_s3_bucket != ""
}

data "aws_iam_policy_document" "cicd_terraform_state" {
  count = local.cicd_terraform_state_enabled && !var.cicd_attach_terraform_admin_policy ? 1 : 0

  # ListBucket must apply only to the bucket ARN; object actions use bucket/*
  statement {
    sid       = "TerraformStateS3List"
    effect    = "Allow"
    actions   = ["s3:ListBucket"]
    resources = ["arn:aws:s3:::${var.cicd_terraform_state_s3_bucket}"]
  }
  statement {
    sid    = "TerraformStateS3Objects"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
    ]
    resources = ["arn:aws:s3:::${var.cicd_terraform_state_s3_bucket}/*"]
  }

  statement {
    sid    = "TerraformStateDynamo"
    effect = "Allow"
    actions = [
      "dynamodb:DescribeTable",
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:DeleteItem",
    ]
    resources = [
      "arn:aws:dynamodb:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:table/${var.cicd_terraform_dynamodb_table}"
    ]
  }

  statement {
    sid     = "STS"
    effect  = "Allow"
    actions = ["sts:GetCallerIdentity"]
    resources = ["*"]
  }

  statement {
    sid    = "EcsTaskDefinitions"
    effect = "Allow"
    actions = [
      "ecs:RegisterTaskDefinition",
      "ecs:DescribeTaskDefinition",
      "ecs:ListTaskDefinitions",
      "ecs:TagResource",
    ]
    resources = ["*"]
  }

  statement {
    sid    = "SecretsForTaskdef"
    effect = "Allow"
    actions = [
      "secretsmanager:DescribeSecret",
      "secretsmanager:GetSecretValue",
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "cicd_terraform_state_min" {
  count  = local.cicd_terraform_state_enabled && !var.cicd_attach_terraform_admin_policy ? 1 : 0
  name   = "cicd-terraform-state-and-ecs"
  role   = aws_iam_role.github_actions_deploy.id
  policy = data.aws_iam_policy_document.cicd_terraform_state[0].json
}

# Broad but standard for dev: lets GitHub run full `terraform plan/apply` in envs/dev in CI.
# Narrow alternative: set cicd_attach_terraform_admin_policy = false; use the inline policy above only
# and run most Terraform from your machine.
resource "aws_iam_role_policy_attachment" "github_terraform_full_access" {
  count      = local.cicd_terraform_state_enabled && var.cicd_attach_terraform_admin_policy ? 1 : 0
  role       = aws_iam_role.github_actions_deploy.name
  policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"
}
