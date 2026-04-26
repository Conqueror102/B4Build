variable "project_name" {
  type    = string
  default = "b4build"
}

variable "environment" {
  type        = string
  description = "Label for AWS resources and tags (e.g. dev, staging)"
  default     = "dev"
}

# Must be one of development | staging | production (matches backend Settings.app_env)
variable "app_env" {
  type        = string
  description = "Runtime APP_ENV for the Python app (CORS, is_production, etc.)"
  default     = "staging"
}

variable "aws_region" {
  type    = string
  default = "us-east-1"
}

variable "availability_zones" {
  type    = list(string)
  default = ["us-east-1a", "us-east-1b"]
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  type    = list(string)
  default = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  type    = list(string)
  default = ["10.0.11.0/24", "10.0.12.0/24"]
}

variable "ecr_repository_name" {
  description = "Must match infra/shared ECR (default b4build/backend)"
  type        = string
  default     = "b4build/backend"
}

# Pinned in CI: deploy-backend sets this to the git commit SHA. Local apply often uses "latest".
variable "ecr_image_tag" {
  description = "ECR image tag for the backend and migration tasks (e.g. git sha or 'latest')."
  type        = string
  default     = "latest"
}

# Optional API hostname (ACM in ALB account/region; DNS validation at registrar, not Route 53)
variable "api_fqdn" {
  description = "E.g. api.example.com. Leave empty for HTTP-only ALB until you have a domain."
  type        = string
  default     = ""
}

# After ACM shows ISSUED, set true and apply again to add HTTPS listener + (optional) redirect
variable "enable_https_listener" {
  type    = bool
  default = false
}

variable "fargate_cpu" {
  type    = number
  default = 512
}

variable "fargate_memory" {
  type    = number
  default = 1024
}

variable "container_port" {
  type    = number
  default = 8000
}

variable "health_check_path" {
  type    = string
  default = "/health"
}

variable "fargate_desired_count" {
  type    = number
  default = 1
}

variable "fargate_max_capacity" {
  type    = number
  default = 4
}

variable "fargate_min_capacity" {
  type    = number
  default = 1
}

# --- AWS Amplify: app only. Connect Git in AWS console when your repo is ready. ---
variable "create_amplify_app" {
  type        = bool
  description = "Create Amplify (NEXT_PUBLIC_API_URL -> ALB). Git is connected in the console, not in Terraform."
  default     = true
}

variable "next_public_clerk_publishable_key" {
  type        = string
  description = "Optional. Syncs to Amplify. Safe to be public (publishable key)."
  default     = ""
}
