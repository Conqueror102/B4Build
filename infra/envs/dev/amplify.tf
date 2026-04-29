# AWS Amplify (Next.js). Terraform creates the app, env, and build instructions only.
# After you create a GitHub repo: Amplify console → "Host web app" / your app → Connect branch → pick repo + main. No PAT in Terraform.

# Fetch Clerk secret from Secrets Manager
data "aws_secretsmanager_secret" "clerk_secret" {
  count = var.create_amplify_app ? 1 : 0
  name  = "/${var.project_name}/${var.environment}/clerk-secret-key"
}

data "aws_secretsmanager_secret_version" "clerk_secret" {
  count     = var.create_amplify_app ? 1 : 0
  secret_id = data.aws_secretsmanager_secret.clerk_secret[0].id
}

locals {
  # Browser must call the API over HTTPS when the page itself is on HTTPS (Amplify), or it
  # gets blocked as mixed content. Preference order:
  #   1. CloudFront (free *.cloudfront.net cert, no domain needed) — default for this env
  #   2. ALB HTTPS via your own domain (api_fqdn + enable_https_listener) — future custom domain
  #   3. ALB HTTP only — local/dev fallback when neither is set up yet
  api_base_url = (
    var.create_cloudfront && length(aws_cloudfront_distribution.api) > 0
    ) ? "https://${aws_cloudfront_distribution.api[0].domain_name}" : (
    (var.api_fqdn != "" && var.enable_https_listener)
    ? "https://${var.api_fqdn}"
    : "http://${aws_lb.main.dns_name}"
  )

  amplify_env = merge(
    {
      NEXT_PUBLIC_API_URL = local.api_base_url
    },
    var.next_public_clerk_publishable_key != "" ? { NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = var.next_public_clerk_publishable_key } : {},
    var.create_amplify_app ? { CLERK_SECRET_KEY = data.aws_secretsmanager_secret_version.clerk_secret[0].secret_string } : {}
  )
}

resource "aws_amplify_app" "web" {
  count = var.create_amplify_app ? 1 : 0

  name     = "${local.name_prefix}-web"
  description = "Next.js app — connect Git in console after the repo exists"
  platform    = "WEB_COMPUTE"

  environment_variables = local.amplify_env

  # Build spec matches amplify.yml in repo root
  build_spec = <<-EOT
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - nvm use 20 || true
        - corepack enable
        - corepack prepare pnpm@9.15.9 --activate
        - cd frontend && pnpm install --frozen-lockfile
    build:
      commands:
        - cd frontend && pnpm run build
  artifacts:
    baseDirectory: frontend/.next
    files:
      - '**/*'
  cache:
    paths:
      - frontend/node_modules/**/*
      - frontend/.next/cache/**/*
EOT

  depends_on = [aws_lb.main]
}
