# Initial secret values are placeholders: replace in AWS console or `aws secretsmanager put-secret-value`
# lifecycle ignore prevents Terraform from clobbering real keys after the first set.

resource "random_password" "db" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_secretsmanager_secret" "openai" {
  name = "${var.project_name}/${var.environment}/openai-api-key"
  recovery_window_in_days   = 0
}

resource "aws_secretsmanager_secret_version" "openai" {
  secret_id     = aws_secretsmanager_secret.openai.id
  secret_string = "REPLACE_WITH_OPENAI_KEY"
  lifecycle {
    ignore_changes = [secret_string]
  }
}

resource "aws_secretsmanager_secret" "tavily" {
  name                    = "${var.project_name}/${var.environment}/tavily-api-key"
  recovery_window_in_days = 0
}
resource "aws_secretsmanager_secret_version" "tavily" {
  secret_id     = aws_secretsmanager_secret.tavily.id
  secret_string = "REPLACE_WITH_TAVILY_KEY"
  lifecycle {
    ignore_changes = [secret_string]
  }
}

resource "aws_secretsmanager_secret" "clerk" {
  name                    = "${var.project_name}/${var.environment}/clerk-secret-key"
  recovery_window_in_days = 0
}
resource "aws_secretsmanager_secret_version" "clerk" {
  secret_id     = aws_secretsmanager_secret.clerk.id
  secret_string = "REPLACE_WITH_CLERK_SECRET"
  lifecycle {
    ignore_changes = [secret_string]
  }
}

resource "aws_secretsmanager_secret" "sentry" {
  name                    = "${var.project_name}/${var.environment}/sentry-dsn"
  recovery_window_in_days = 0
}
resource "aws_secretsmanager_secret_version" "sentry" {
  secret_id     = aws_secretsmanager_secret.sentry.id
  secret_string = "REPLACE_WITH_SENTRY_DSN"
  lifecycle {
    ignore_changes = [secret_string]
  }
}

resource "aws_secretsmanager_secret" "langsmith" {
  name                    = "${var.project_name}/${var.environment}/langsmith-api-key"
  recovery_window_in_days = 0
}

resource "aws_secretsmanager_secret_version" "langsmith" {
  secret_id     = aws_secretsmanager_secret.langsmith.id
  secret_string = "REPLACE_WITH_LANGSMITH_API_KEY"
  lifecycle {
    ignore_changes = [secret_string]
  }
}

resource "aws_secretsmanager_secret" "database_url" {
  name                    = "${var.project_name}/${var.environment}/database-url"
  recovery_window_in_days = 0
}

# Version updated after RDS exists (url uses endpoint + same password as RDS)
resource "aws_secretsmanager_secret_version" "database_url" {
  secret_id     = aws_secretsmanager_secret.database_url.id
  secret_string = local.database_url
  depends_on    = [module.db]
  lifecycle {
    ignore_changes  = [secret_string]
  }
}

locals {
  # Percent-encode special chars in password for URL. `ssl=true` is required for RDS
  # (otherwise "no pg_hba... no encryption" with asyncpg).
  database_url = format(
    "postgresql://%s:%s@%s:%s/%s?ssl=true",
    "b4build_admin",
    urlencode(random_password.db.result),
    module.db.db_instance_address,
    tostring(module.db.db_instance_port),
    coalesce(module.db.db_instance_name, "b4build")
  )
}
