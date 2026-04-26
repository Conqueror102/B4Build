.PHONY: help init plan apply destroy fmt validate clean

# Default target
help:
	@echo "B4Build Infrastructure Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make init       Initialize Terraform"
	@echo "  make plan       Run Terraform plan"
	@echo "  make apply      Apply Terraform changes"
	@echo "  make destroy    Destroy infrastructure"
	@echo "  make fmt        Format Terraform files"
	@echo "  make validate   Validate Terraform configuration"
	@echo "  make clean      Clean Terraform cache"
	@echo ""
	@echo "Targets:"
	@echo "  shared          Work with shared resources (ECR, OIDC)"
	@echo "  dev             Work with dev environment"

# Shared resources
init-shared:
	cd shared && terraform init

plan-shared:
	cd shared && terraform plan

apply-shared:
	cd shared && terraform apply

destroy-shared:
	cd shared && terraform destroy

# Dev environment
init-dev:
	cd envs/dev && terraform init

plan-dev:
	cd envs/dev && terraform plan

apply-dev:
	cd envs/dev && terraform apply

destroy-dev:
	cd envs/dev && terraform destroy

# Convenience targets
init: init-shared init-dev

plan: plan-dev

apply: apply-dev

destroy: destroy-dev

# Format all Terraform files
fmt:
	terraform fmt -recursive .

# Validate all configurations
validate:
	cd shared && terraform validate
	cd envs/dev && terraform validate

# Clean Terraform cache
clean:
	find . -type d -name ".terraform" -exec rm -rf {} +
	find . -type f -name "*.tfstate*" -delete
	find . -type f -name "*.tfplan" -delete

# Output dev environment info
output:
	cd envs/dev && terraform output deployment_summary
