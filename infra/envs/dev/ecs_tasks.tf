resource "aws_ecs_cluster" "this" {
  name = local.cluster_name

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

resource "aws_ecs_task_definition" "backend" {
  family                   = "${local.name_prefix}-backend"
  network_mode             = "awsvpc"
  requires_compatibilities  = ["FARGATE"]
  cpu                      = var.fargate_cpu
  memory                   = var.fargate_memory
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name  = "backend"
      image = "${data.aws_ecr_repository.backend.repository_url}:${var.ecr_image_tag}"
      essential = true
      portMappings = [
        { containerPort = var.container_port, hostPort = var.container_port, protocol = "tcp" }
      ]
      environment = [
        { name = "APP_ENV", value = var.app_env },
        { name = "AWS_DEFAULT_REGION", value = var.aws_region },
        { name = "S3_BUCKET_NAME", value = aws_s3_bucket.pdfs.id },
        { name = "REDIS_URL", value = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:${tostring(aws_elasticache_cluster.redis.port)}" }
      ]
      secrets = [
        { name = "OPENAI_API_KEY", valueFrom = aws_secretsmanager_secret.openai.arn },
        { name = "TAVILY_API_KEY", valueFrom = aws_secretsmanager_secret.tavily.arn },
        { name = "CLERK_SECRET_KEY", valueFrom = aws_secretsmanager_secret.clerk.arn },
        { name = "SENTRY_DSN", valueFrom = aws_secretsmanager_secret.sentry.arn },
        { name = "DATABASE_URL", valueFrom = aws_secretsmanager_secret.database_url.arn }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "backend"
        }
      }
      healthCheck = {
        command  = ["CMD-SHELL", "curl -f http://localhost:${var.container_port}${var.health_check_path} || exit 1"]
        interval = 30
        timeout  = 5
        retries  = 3
        startPeriod = 90
      }
    }
  ])
}

# One-off: aws ecs run-task (see ../README)
resource "aws_ecs_task_definition" "migrations" {
  family                   = "${local.name_prefix}-migrations"
  network_mode             = "awsvpc"
  requires_compatibilities  = ["FARGATE"]
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([
    {
      name  = "migrations"
      image = "${data.aws_ecr_repository.backend.repository_url}:${var.ecr_image_tag}"
      essential = true
      # Same env/secrets as the API so database URL and settings resolve
      environment = [
        { name = "APP_ENV", value = var.app_env },
        { name = "AWS_DEFAULT_REGION", value = var.aws_region },
        { name = "S3_BUCKET_NAME", value = aws_s3_bucket.pdfs.id },
        { name = "REDIS_URL", value = "redis://${aws_elasticache_cluster.redis.cache_nodes[0].address}:${tostring(aws_elasticache_cluster.redis.port)}" }
      ]
      secrets = [
        { name = "OPENAI_API_KEY", valueFrom = aws_secretsmanager_secret.openai.arn },
        { name = "TAVILY_API_KEY", valueFrom = aws_secretsmanager_secret.tavily.arn },
        { name = "CLERK_SECRET_KEY", valueFrom = aws_secretsmanager_secret.clerk.arn },
        { name = "SENTRY_DSN", valueFrom = aws_secretsmanager_secret.sentry.arn },
        { name = "DATABASE_URL", valueFrom = aws_secretsmanager_secret.database_url.arn }
      ]
      command   = ["/bin/sh", "-c", "cd /app && /app/.venv/bin/alembic upgrade head && echo done"]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "migrate"
        }
      }
    }
  ])
}
