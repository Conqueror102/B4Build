# Quick Start Guide

## TL;DR - Deploy in 10 Commands

```bash
# 1. Create state backend
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUCKET="b4build-terraform-state-${ACCOUNT_ID}"
aws s3api create-bucket --bucket $BUCKET --region us-east-1
aws s3api put-bucket-versioning --bucket $BUCKET --versioning-configuration Status=Enabled
aws dynamodb create-table --table-name b4build-terraform-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST --region us-east-1

# 2. Update backend.tf files with bucket name
sed -i "s/YOUR_BUCKET_NAME_HERE/$BUCKET/g" infra/shared/backend.tf
sed -i "s/YOUR_BUCKET_NAME_HERE/$BUCKET/g" infra/envs/dev/backend.tf

# 3. Deploy shared resources
cd infra/shared && terraform init && terraform apply -auto-approve

# 4. Store secrets
aws secretsmanager create-secret --name b4build/dev/openai-api-key --secret-string "sk-..."
aws secretsmanager create-secret --name b4build/dev/clerk-secret-key --secret-string "sk_..."
aws secretsmanager create-secret --name b4build/dev/tavily-api-key --secret-string "tvly-..."

# 5. Deploy dev environment (takes ~15 min)
cd ../envs/dev && terraform init && terraform apply -auto-approve

# 6. Build & push backend
cd ../../../backend
ECR=$(cd ../infra/shared && terraform output -raw ecr_repository_url)
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR
docker build -t b4build-backend . && docker tag b4build-backend:latest $ECR:latest
docker push $ECR:latest

# 7. Deploy to ECS
aws ecs update-service --cluster b4build-dev --service b4build-backend --force-new-deployment --region us-east-1

# 8. Test
ALB=$(cd ../infra/envs/dev && terraform output -raw alb_dns_name)
curl http://$ALB/health

# 9. Deploy frontend (Vercel)
cd ../frontend && vercel --prod
# Set NEXT_PUBLIC_API_URL=http://$ALB in Vercel dashboard

# 10. Done! 🎉
```

## What You Get

- ✅ VPC with public/private subnets (Multi-AZ)
- ✅ NAT Gateway for private subnet internet access
- ✅ RDS Postgres (Multi-AZ, encrypted)
- ✅ ElastiCache Redis
- ✅ ECS Fargate (auto-scaling)
- ✅ Application Load Balancer
- ✅ CloudFront CDN
- ✅ WAF with OWASP rules
- ✅ S3 for PDFs
- ✅ CloudWatch monitoring + alarms

## Cost: ~$4/day (~$122/month)

## Cleanup

```bash
cd infra/envs/dev && terraform destroy -auto-approve
cd ../../shared && terraform destroy -auto-approve
aws s3 rb s3://$BUCKET --force
aws dynamodb delete-table --table-name b4build-terraform-lock
```

## Troubleshooting

**ECS tasks not starting?**
```bash
aws logs tail /ecs/b4build-dev --follow
```

**Health checks failing?**
```bash
aws elbv2 describe-target-health --target-group-arn $(aws elbv2 describe-target-groups --names b4build-dev-tg --query 'TargetGroups[0].TargetGroupArn' --output text)
```

**Need to update secrets?**
```bash
aws secretsmanager update-secret --secret-id b4build/dev/openai-api-key --secret-string "new-key"
```

## Key URLs

After deployment, get these from Terraform outputs:

```bash
cd infra/envs/dev
terraform output deployment_summary
```

- Backend API: `http://[ALB_DNS]/health`
- PDF CDN: `https://[CLOUDFRONT_DOMAIN]`
- Logs: CloudWatch → `/ecs/b4build-dev`
- Metrics: CloudWatch → ECS Container Insights
