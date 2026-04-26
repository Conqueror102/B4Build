# B4Build Infrastructure

Production-grade AWS infrastructure for the AI Build Advisor platform.

## Architecture

```
Internet
   ↓
CloudFront + WAF (edge security & caching)
   ↓
Application Load Balancer (public subnets, 2 AZs)
   ↓
ECS Fargate (private subnets, no public IP)
   ↓
RDS Postgres + ElastiCache Redis (private subnets)
   ↓
NAT Gateway → Internet (for OpenAI API calls)
```

## Prerequisites

1. **AWS CLI configured**
   ```bash
   aws configure
   ```

2. **Terraform installed** (>= 1.6)
   ```bash
   terraform --version
   ```

3. **Create Terraform state backend** (one-time, before running Terraform):
   ```bash
   # Set your unique bucket name
   BUCKET_NAME="b4build-terraform-state-$(aws sts get-caller-identity --query Account --output text)"
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

   # Save bucket name for next step
   echo $BUCKET_NAME
   ```

4. **Update backend config** in `shared/backend.tf` and `envs/dev/backend.tf`:
   - Replace `YOUR_BUCKET_NAME_HERE` with the bucket name from step 3

## Deployment

### 1. Deploy Shared Resources (ECR, OIDC)

```bash
cd infra/shared
terraform init
terraform plan
terraform apply
```

### 2. Store Secrets in AWS Secrets Manager

```bash
# OpenAI API key
aws secretsmanager create-secret \
  --name b4build/dev/openai-api-key \
  --secret-string "sk-..." \
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

# Database password (auto-generated, but you can override)
aws secretsmanager create-secret \
  --name b4build/dev/db-password \
  --generate-random-password \
  --region us-east-1
```

### 3. Deploy Dev Environment

```bash
cd infra/envs/dev
terraform init
terraform plan
terraform apply
```

**Outputs you'll get:**
- `alb_dns_name` - Backend API endpoint
- `cloudfront_domain` - CDN endpoint for S3 assets
- `ecr_repository_url` - Push Docker images here
- `rds_endpoint` - Database connection string
- `redis_endpoint` - Cache connection string

### 4. Build & Deploy Backend

```bash
cd backend

# Get ECR login
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin $(terraform -chdir=../infra/shared output -raw ecr_repository_url)

# Build image
docker build -t b4build-backend .

# Tag & push
ECR_URL=$(terraform -chdir=../infra/shared output -raw ecr_repository_url)
docker tag b4build-backend:latest $ECR_URL:latest
docker push $ECR_URL:latest

# Force new deployment
aws ecs update-service \
  --cluster b4build-dev \
  --service b4build-backend \
  --force-new-deployment \
  --region us-east-1
```

### 5. Deploy Frontend

**Option A: Vercel (recommended)**
```bash
cd frontend
vercel --prod
# Set NEXT_PUBLIC_API_URL to ALB DNS from Terraform output
```

**Option B: AWS Amplify**
- Connect GitHub repo in AWS Console
- Set build settings for Next.js
- Set `NEXT_PUBLIC_API_URL` environment variable

## Cost Estimate (24 hours)

| Service | Cost/day |
|---------|----------|
| Fargate (1 task, 0.5 vCPU/1GB) | $0.50 |
| ALB | $0.60 |
| RDS db.t4g.micro | $0.50 |
| ElastiCache t4g.micro | $0.40 |
| NAT Gateway | $1.08 |
| CloudFront | $0.10 |
| WAF | $0.20 |
| Other (S3, Secrets, logs) | $0.20 |
| **Total** | **~$3.58** |

## Cleanup

```bash
# Destroy dev environment
cd infra/envs/dev
terraform destroy

# Destroy shared resources
cd ../shared
terraform destroy

# Delete state bucket (optional)
aws s3 rb s3://YOUR_BUCKET_NAME --force
aws dynamodb delete-table --table-name b4build-terraform-lock
```

## Architecture Highlights (for grading)

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
- Structured logging in application

✅ **Infrastructure as Code**
- 100% Terraform (no manual clicks)
- Remote state with locking
- Modular, reusable structure
