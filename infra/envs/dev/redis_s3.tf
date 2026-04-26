resource "aws_elasticache_subnet_group" "redis" {
  name        = replace("${local.name_prefix}-redis-sub", "_", "-")
  description = "Redis for ${local.name_prefix}"
  subnet_ids  = module.vpc.private_subnets
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id         = replace("${var.project_name}-${var.environment}-redis", "_", "-")
  engine             = "redis"
  node_type          = "cache.t4g.micro"
  num_cache_nodes    = 1
  engine_version     = "7.1"
  port               = 6379
  parameter_group_name = "default.redis7"
  subnet_group_name  = aws_elasticache_subnet_group.redis.name
  security_group_ids  = [aws_security_group.redis.id]
  maintenance_window  = "sun:05:00-sun:06:00"
  snapshot_window     = "03:00-04:00"
  snapshot_retention_limit = 5
  apply_immediately = true
}

# Private PDFs — access via Fargate task role or presigned URLs from app
resource "aws_s3_bucket" "pdfs" {
  bucket = "${local.name_prefix}-pdfs-${data.aws_caller_identity.current.account_id}"
}

resource "aws_s3_bucket_public_access_block" "pdfs" {
  bucket = aws_s3_bucket.pdfs.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "pdfs" {
  bucket = aws_s3_bucket.pdfs.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}
