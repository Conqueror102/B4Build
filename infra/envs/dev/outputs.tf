output "acm_validation_records" {
  description = "Add these CNAME records at your domain registrar to validate the ACM cert (no Route 53 in this stack)."
  value = var.api_fqdn == "" ? [] : [for o in try(aws_acm_certificate.api[0].domain_validation_options, []) : {
    name  = o.resource_record_name
    value = o.resource_record_value
    type  = o.resource_record_type
  }]
}

output "alb_http_url" {
  value = "http://${aws_lb.main.dns_name}"
}

output "alb_dns_name" {
  description = "Set NEXT_PUBLIC_API_URL to this (or https if you enable the 443 listener)."
  value       = aws_lb.main.dns_name
}

output "ecs_cluster_name" {
  value = aws_ecs_cluster.this.name
}

output "ecs_service_name" {
  value = aws_ecs_service.backend.name
}

output "migrations_task_definition" {
  value = aws_ecs_task_definition.migrations.arn
}

output "migrations_run_command" {
  description = "Run DB migrations (private subnets, no public IP — run from a bastion, VPN, or Systems Manager as needed)"
  value       = <<EOT
Set SUBNETS to two private subnet IDs (terraform output private_subnet_ids) and SG to the Fargate security group.
aws ecs run-task --cluster ${aws_ecs_cluster.this.name} --launch-type FARGATE --task-definition ${aws_ecs_task_definition.migrations.family} --network-configuration "awsvpcConfiguration={subnets=[SUBNET1,SUBNET2],securityGroups=[${aws_security_group.fargate.id}],assignPublicIp=DISABLED}"
EOT
}

output "private_subnet_ids" {
  value = module.vpc.private_subnets
}

output "fargate_security_group_id" {
  value = aws_security_group.fargate.id
}

output "rds_endpoint" {
  value = module.db.db_instance_endpoint
  sensitive = true
}

output "s3_pdfs_bucket" {
  value = aws_s3_bucket.pdfs.id
}

output "redis_address" {
  value = "${aws_elasticache_cluster.redis.cache_nodes[0].address}:${tostring(aws_elasticache_cluster.redis.port)}"
}

output "amplify_app_id" {
  description = "Amplify app (only if create_amplify_app = true)"
  value       = length(aws_amplify_app.web) > 0 ? aws_amplify_app.web[0].id : null
}

output "amplify_default_domain" {
  description = "App hub domain (connect a branch to get main.xxx.amplifyapp.com)"
  value       = length(aws_amplify_app.web) > 0 ? aws_amplify_app.web[0].default_domain : null
}
