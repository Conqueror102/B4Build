output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}

output "alb_dns_name" {
  description = "ALB DNS name (use this as your backend API endpoint)"
  value       = aws_lb.main.dns_name
}

output "alb_url" {
  description = "ALB URL"
  value       = "http://${aws_lb.main.dns_name}"
}

output "cloudfront_domain" {
  description = "CloudFront distribution domain for PDFs"
  value       = aws_cloudfront_distribution.pdfs.domain_name
}

output "cloudfront_url" {
  description = "CloudFront URL"
  value       = "https://${aws_cloudfront_distribution.pdfs.domain_name}"
}

output "rds_endpoint" {
  description = "RDS endpoint"
  value       = aws_db_instance.main.endpoint
}

output "rds_database_name" {
  description = "RDS database name"
  value       = aws_db_instance.main.db_name
}

output "rds_username" {
  description = "RDS username"
  value       = aws_db_instance.main.username
  sensitive   = true
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = "${aws_elasticache_cluster.main.cache_nodes[0].address}:${aws_elasticache_cluster.main.cache_nodes[0].port}"
}

output "s3_bucket_name" {
  description = "S3 bucket name for PDFs"
  value       = aws_s3_bucket.pdfs.id
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN"
  value       = aws_s3_bucket.pdfs.arn
}

output "ecs_cluster_name" {
  description = "ECS cluster name"
  value       = aws_ecs_cluster.main.name
}

output "ecs_service_name" {
  description = "ECS service name"
  value       = aws_ecs_service.backend.name
}

output "waf_web_acl_id" {
  description = "WAF Web ACL ID"
  value       = aws_wafv2_web_acl.main.id
}

output "waf_web_acl_arn" {
  description = "WAF Web ACL ARN"
  value       = aws_wafv2_web_acl.main.arn
}

output "deployment_summary" {
  description = "Deployment summary"
  value = <<-EOT
    ========================================
    B4Build Infrastructure Deployed
    ========================================
    
    Backend API:
      URL: http://${aws_lb.main.dns_name}
      Health: http://${aws_lb.main.dns_name}/health
    
    PDF CDN:
      URL: https://${aws_cloudfront_distribution.pdfs.domain_name}
    
    Database:
      Endpoint: ${aws_db_instance.main.endpoint}
      Database: ${aws_db_instance.main.db_name}
    
    Cache:
      Endpoint: ${aws_elasticache_cluster.main.cache_nodes[0].address}:${aws_elasticache_cluster.main.cache_nodes[0].port}
    
    Storage:
      S3 Bucket: ${aws_s3_bucket.pdfs.id}
    
    Security:
      WAF: Enabled (OWASP rules + rate limiting)
      Encryption: At rest + in transit
    
    Next Steps:
      1. Build & push Docker image to ECR
      2. Update ECS service to deploy
      3. Set NEXT_PUBLIC_API_URL in frontend
      4. Test: curl http://${aws_lb.main.dns_name}/health
    
    ========================================
  EOT
}
