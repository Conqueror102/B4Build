module "db" {
  source  = "terraform-aws-modules/rds/aws"
  version = "~> 6.0"

  identifier = "${local.name_prefix}-db"

  create_db_option_group  = false
  create_db_parameter_group = true
  family  = "postgres16"
  parameters = []

  engine         = "postgres"
  engine_version  = "16" # use latest 16.x available in the region; pin if you need
  instance_class  = "db.t4g.micro"
  major_engine_version = "16"
  allocated_storage  = 20
  max_allocated_storage = 100
  storage_type          = "gp3"
  storage_encrypted     = true

  db_name  = "b4build"
  username = "b4build_admin"
  port     = 5432
  password = random_password.db.result
  multi_az = false

  create_db_subnet_group  = true
  subnet_ids              = module.vpc.private_subnets
  vpc_security_group_ids  = [aws_security_group.rds.id]
  publicly_accessible     = false

  enabled_cloudwatch_logs_exports = ["postgresql", "upgrade"]
  performance_insights_enabled    = true
  performance_insights_retention_period = 7

  backup_window              = "03:00-04:00"
  maintenance_window         = "mon:04:00-mon:05:00"
  backup_retention_period  = 7
  skip_final_snapshot      = true
  deletion_protection         = false

  # Cost / ops for a portfolio: no enhanced monitoring
  create_monitoring_role  = false
  monitoring_interval      = 0
}
