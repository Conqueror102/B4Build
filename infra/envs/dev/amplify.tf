# AWS Amplify (Next.js). Terraform creates the app, env, and build instructions only.
# After you create a GitHub repo: Amplify console → "Host web app" / your app → Connect branch → pick repo + main. No PAT in Terraform.

locals {
  amplify_env = merge(
    {
      NEXT_PUBLIC_API_URL = "http://${aws_lb.main.dns_name}"
    },
    var.next_public_clerk_publishable_key != "" ? { NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY = var.next_public_clerk_publishable_key } : {}
  )
}

resource "aws_amplify_app" "web" {
  count = var.create_amplify_app ? 1 : 0

  name     = "${local.name_prefix}-web"
  description = "Next.js app — connect Git in console after the repo exists"
  platform    = "WEB_COMPUTE"

  environment_variables = local.amplify_env

  # Build until amplify.yml in the repository root (added in this monorepo) is picked up
  build_spec = <<-EOT
version: 1
frontend:
  phases:
    preBuild:
      commands:
        - nvm use 20 || true
        - cd frontend && npm ci
    build:
      commands:
        - cd frontend && npm run build
  artifacts:
    baseDirectory: frontend
    files:
      - '**/*'
  cache:
    paths:
      - frontend/node_modules/**/*
EOT

  depends_on = [aws_lb.main]
}
