resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"

  client_id_list = [
    "sts.amazonaws.com"
  ]

  # GitHub Actions OIDC thumbprint (as of 2023+)
  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1"
  ]
}

# Least-privilege role for ECR push + rolling ECS deploy (no full ECS/EC2 admin)
resource "aws_iam_role" "github_actions_deploy" {
  name = "b4build-github-actions-deploy"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = "sts:AssumeRoleWithWebIdentity"
        Principal = {
          Federated = aws_iam_openid_connect_provider.github.arn
        }
        Condition = {
          StringEquals = {
            "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
          }
          StringLike = {
            "token.actions.githubusercontent.com:sub" = "repo:${var.github_org}/${var.github_repo}:*"
          }
        }
      }
    ]
  })
}

# Allow pushing images to this ECR repository only
resource "aws_iam_role_policy" "github_ecr" {
  name = "ecr-push"
  role = aws_iam_role.github_actions_deploy.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ecr:GetAuthorizationToken"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:CompleteLayerUpload",
          "ecr:InitiateLayerUpload",
          "ecr:PutImage",
          "ecr:UploadLayerPart",
          "ecr:BatchGetImage"
        ]
        Resource = [
          aws_ecr_repository.backend.arn
        ]
      }
    ]
  })
}

data "aws_caller_identity" "current" {}
data "aws_region" "current" {}

locals {
  # Match .github/workflows/deploy-backend.yml: cluster b4build-dev, service b4build-backend
  account_id  = data.aws_caller_identity.current.account_id
  region_id   = data.aws_region.current.id
  # ECS service full ARN format (used by IAM for some actions)
  service_name_pattern = "arn:aws:ecs:${local.region_id}:${local.account_id}:service/b4build-dev/b4build-backend"
  ecs_task_exec_name   = "b4build-dev-ecs-execution"
  ecs_task_name        = "b4build-dev-ecs-task"
  ecs_task_exec_arn    = "arn:aws:iam::${local.account_id}:role/${local.ecs_task_exec_name}"
  ecs_task_role_arn    = "arn:aws:iam::${local.account_id}:role/${local.ecs_task_name}"
}

resource "aws_iam_role_policy" "github_ecs" {
  name = "ecs-deploy"
  role = aws_iam_role.github_actions_deploy.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect   = "Allow"
        Action   = ["ecs:UpdateService"]
        Resource = [local.service_name_pattern]
      },
      {
        Effect   = "Allow"
        Action = [
          "ecs:DescribeServices",
          "ecs:DescribeClusters",
          "ecs:DescribeTaskDefinition",
          "ecs:ListTaskDefinitions",
          "ecs:ListTasks",
          "ecs:DescribeTasks"
        ]
        Resource = ["*"]
      },
      {
        Effect   = "Allow"
        Action   = "iam:PassRole"
        Resource = [local.ecs_task_exec_arn, local.ecs_task_role_arn]
        Condition = {
          StringEquals = {
            "iam:PassedToService" = "ecs-tasks.amazonaws.com"
          }
        }
      }
    ]
  })
}

# Optional: if PassRole with wildcards is needed, document — first deploy may use placeholder ARNs; user re-applies oidc with exact ARNs from Terraform outputs
# Simpler fix: use broader PassRole to account task roles (still scoped)
resource "aws_iam_role_policy" "github_logs" {
  name = "cloudwatch-logs"
  role = aws_iam_role.github_actions_deploy.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
      Resource = "arn:aws:logs:${data.aws_region.current.id}:${data.aws_caller_identity.current.account_id}:log-group:/ecs/*"
    }]
  })
}
