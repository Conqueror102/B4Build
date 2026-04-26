# B4Build AWS Deployment Guide

Complete guide to deploying the AI Build Advisor on AWS with Terraform.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         Internet                             │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────▼──────────┐
         │   CloudFront + WAF   │  ← Edge caching + security
         └───────────┬──────────┘
                     │
         ┌───────────▼──────────┐
         │   Application LB     │  ← Public subnets (2 AZs)
         └───────────┬──────────┘
                     │
    ┌────────────────▼────────────────┐
    │  ECS Fargate Tasks              │  ← Private subnets
    │  (Python backend)               │     (no public IP)
    └─────┬──────────────────┬────────┘
          │                  │
    ┌─────▼─────┐      ┌────▼────────┐
    │    RDS    │      │ ElastiCache │
    │ Postgres  │      │    Redis    │
    │ (Multi-AZ)│      │             │
    └───────────┘      └─────────────┘
          │
    ┌─────▼─────┐
    │    NAT    │  ← Private → Internet (OpenAI API)
    │  Gateway  │
    └─────┬─────┘
          │
    ┌─────▼─────┐
    │ Internet  │
    │  Gateway  │
    └───────────┘
```

## Production Features

✅ **Network Security**
- Private subnets for backend (no public IP)
- NAT Gateway for outbound internet
- Security groups with least-privilege rules

✅ **High Availability**
- Multi-AZ deployment (2 availability zones)
- RDS with automated backups
- ALB health checks + auto-recovery

✅ **Security**
- WAF with OWASP rules + rate limiting
- Secrets Manager (no hardcoded credentials)
- IAM roles (no access keys)
- Encryption at rest (RDS, S3, Secrets)
- Encryption in transit (HTTPS only)

✅ **Scalability**
- ECS auto-scaling based on CPU/memory
- CloudFront edge caching
- Redis for session/rate limit caching

✅ **Observability**
- CloudWatch Logs for all services
- CloudWatch Alarms for critical metrics
- VPC Flow Logs
- WAF logging

## Prerequisites

### 1. Install Tools

**macOS:**
```bash
brew install awscli terraform
```

**Windows:**
```powershell
choco install awscli terraform
```

**Linux:**
```bash
# AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Terraform
wget https://releases.hashicorp.com/terraform/1.6.0/terraform_1.6.0_linux_amd64.zip
unzip terraform_1.6.0_linux_amd64.zip
sudo mv terraform /usr/local/bin/
```

### 2. Configure AWS CLI

```bash
aws configure
# AWS Access Key ID: [your key]
# AWS Secret Access Key: [your secret]
# Default region name: us-east-1
# Default output format: json
```

### 3. Verify Setup

```bash
aws sts get-caller-identity
terraform --version
```

## Step-by-Step Deployment

### Step 1: Create Terraform State Backend

This is a **one-time setup** before running Terraform:

```bash
# Set your unique bucket name (must be globally unique)
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUCKET_NAME="b4build-terraform-state-${ACCOUNT_ID}"
REGION="us-east-1"

# Create S3 bucket
aws s3api create-bucket \
  --bucket $BUCKET_NAME \
  --region $REGION

# Enable versioning
aws s3api put-bucket-versioning \
  --bucket $BUCKET_NAME \
  --versioning-configuration Status=Enabled

# Enable encryption
aws s3api put-bucket-encryption \
  --bucket $BUCKET_NAME \
  --server-side-encryption-configuration '{
    "Rules": [{
      "ApplyServerSideEncryptionByDefault": {
        "SSEAlgorithm": "AES256"
      }
    }]
  }'

# Block public access
aws s3api put-public-access-block \
  --bucket $BUCKET_NAME \
  --public-access-block-configuration \
    BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true

# Create DynamoDB lock table
aws dynamodb create-table \
  --table-name b4build-terraform-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region $REGION

# Print bucket name (you'll need this next)
echo "Bucket created: $BUCKET_NAME"
```

### Step 2: Update Terraform Backend Config

Update the bucket name in these files:
- `infra/shared/backend.tf`
- `infra/envs/dev/backend.tf`

Replace `YOUR_BUCKET_NAME_HERE` with the bucket name from Step 1.

### Step 3: Deploy Shared Resources (ECR, OIDC)

```bash
cd infra/shared
terraform init
terraform plan
terraform apply
```

**Outputs:**
- `ecr_repository_url` - Docker image repository
- `github_actions_role_arn` - For CI/CD (save this)

### Step 4: Store Secrets in AWS Secrets Manager

```bash
# OpenAI API key
aws secretsmanager create-secret \
  --name b4build/dev/openai-api-key \
  --secret-string "sk-proj-..." \
  --region us-east-1

# Clerk secret key
aws secretsmanager create-secret \
  --name b4build/dev/clerk-secret-key \
  --secret-string "sk_..." \
  --region us-east-1

# Tavily API key
aws secretsmanager create-secret \
  --name b4build/dev/tavily-api-key \
  --secret-string "tvly-..." \
  --region us-east-1
```

**Note:** Database password is auto-generated by Terraform.

### Step 5: Deploy Dev Environment

```bash
cd infra/envs/dev
terraform init
terraform plan
terraform apply
```

This will create:
- VPC with public/private subnets
- NAT Gateway
- RDS Postgres (Multi-AZ)
- ElastiCache Redis
- ECS Fargate cluster
- Application Load Balancer
- CloudFront distribution
- WAF with OWASP rules
- S3 bucket for PDFs
- CloudWatch alarms

**⏱️ Deployment time: ~15-20 minutes** (RDS Multi-AZ takes the longest)

### Step 6: Save Outputs

```bash
# View all outputs
terraform output

# Save important values
ALB_URL=$(terraform output -raw alb_dns_name)
CLOUDFRONT_URL=$(terraform output -raw cloudfront_domain)
ECR_URL=$(cd ../../shared && terraform output -raw ecr_repository_url)

echo "Backend API: http://$ALB_URL"
echo "PDF CDN: https://$CLOUDFRONT_URL"
echo "ECR: $ECR_URL"
```

### Step 7: Build & Deploy Backend

```bash
cd ../../../backend

# Login to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $ECR_URL

# Build image
docker build -t b4build-backend .

# Tag & push
docker tag b4build-backend:latest $ECR_URL:latest
docker push $ECR_URL:latest

# Force ECS to pull new image
aws ecs update-service \
  --cluster b4build-dev \
  --service b4build-backend \
  --force-new-deployment \
  --region us-east-1

# Wait for deployment
aws ecs wait services-stable \
  --cluster b4build-dev \
  --services b4build-backend \
  --region us-east-1
```

### Step 8: Test Backend

```bash
# Health check
curl http://$ALB_URL/health

# Expected response:
# {"status":"healthy"}
```

### Step 9: Deploy Frontend

**Option A: Vercel (Recommended)**
```bash
cd ../frontend
npm install -g vercel
vercel login
vercel --prod

# Set environment variable in Vercel dashboard:
# NEXT_PUBLIC_API_URL=http://[ALB_DNS_FROM_STEP_6]
```

**Option B: AWS Amplify**
1. Go to AWS Amplify Console
2. Connect your GitHub repository
3. Select `frontend` folder as root
4. Add environment variable: `NEXT_PUBLIC_API_URL=http://[ALB_DNS]`
5. Deploy

### Step 10: Setup GitHub Actions (Optional)

1. Add GitHub secret `AWS_ROLE_ARN` with the OIDC role ARN from Step 3
2. Update `infra/shared/oidc.tf` with your GitHub org/repo
3. Push to main branch - CI/CD will auto-deploy

## Cost Breakdown (24 hours)

| Service | Cost/day |
|---------|----------|
| Fargate (1 task, 0.5 vCPU/1GB) | $0.50 |
| ALB | $0.60 |
| RDS db.t4g.micro (Multi-AZ) | $1.00 |
| ElastiCache t4g.micro | $0.40 |
| NAT Gateway | $1.08 |
| CloudFront | $0.10 |
| WAF | $0.20 |
| Other (S3, Secrets, logs) | $0.20 |
| **Total** | **~$4.08/day** |

**Monthly estimate: ~$122**

## Cleanup

```bash
# Destroy dev environment
cd infra/envs/dev
terraform destroy

# Destroy shared resources
cd ../../shared
terraform destroy

# Delete state bucket (optional)
aws s3 rb s3://$BUCKET_NAME --force
aws dynamodb delete-table --table-name b4build-terraform-lock --region us-east-1
```

## Troubleshooting

### ECS tasks not starting
```bash
# Check logs
aws logs tail /ecs/b4build-dev --follow

# Check task status
aws ecs describe-tasks \
  --cluster b4build-dev \
  --tasks $(aws ecs list-tasks --cluster b4build-dev --query 'taskArns[0]' --output text)
```

### ALB health checks failing
```bash
# Check target health
aws elbv2 describe-target-health \
  --target-group-arn $(aws elbv2 describe-target-groups \
    --names b4build-dev-tg \
    --query 'TargetGroups[0].TargetGroupArn' \
    --output text)
```

### Database connection issues
```bash
# Test from Fargate task
aws ecs execute-command \
  --cluster b4build-dev \
  --task [TASK_ID] \
  --container backend \
  --interactive \
  --command "/bin/bash"

# Inside container:
psql $DATABASE_URL
```

### Secrets not loading
```bash
# Verify secrets exist
aws secretsmanager list-secrets --query 'SecretList[?starts_with(Name, `b4build/dev/`)]'

# Check IAM permissions
aws iam get-role-policy \
  --role-name b4build-dev-ecs-task-execution \
  --policy-name secrets-access
```

## Monitoring

### CloudWatch Dashboards
- ECS: Container Insights enabled
- RDS: Performance Insights enabled
- WAF: Request metrics + blocked requests

### Key Alarms
- RDS CPU > 80%
- RDS storage < 2GB
- Redis CPU > 75%
- ALB response time > 1s
- ALB unhealthy targets > 0
- WAF blocked requests > 100/5min

## Security Best Practices

✅ **Implemented:**
- Private subnets for backend
- Secrets Manager for credentials
- IAM roles (no access keys)
- WAF with OWASP rules
- Encryption at rest + in transit
- VPC Flow Logs
- Security groups with least privilege

🔒 **For Production:**
- Enable MFA for AWS accounts
- Enable CloudTrail for audit logs
- Set up AWS Config for compliance
- Enable GuardDuty for threat detection
- Use AWS Certificate Manager for custom domain
- Enable RDS encryption with KMS
- Set up backup retention policies

## Next Steps

1. ✅ Infrastructure deployed
2. ✅ Backend running on Fargate
3. ✅ Frontend deployed
4. 🔄 Add custom domain (Route 53 + ACM)
5. 🔄 Set up monitoring dashboards
6. 🔄 Configure backup policies
7. 🔄 Enable auto-scaling policies
8. 🔄 Set up CI/CD pipelines

## Support

For issues or questions:
1. Check CloudWatch Logs
2. Review Terraform outputs
3. Verify security group rules
4. Check IAM permissions
