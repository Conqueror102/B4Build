# Before You Start - Important Notes

## ⚠️ Critical: Update These Files First

Before running `terraform init`, you **MUST** update the S3 bucket name in these files:

1. `infra/shared/backend.tf` - Line 14: Replace `YOUR_BUCKET_NAME_HERE`
2. `infra/envs/dev/backend.tf` - Line 14: Replace `YOUR_BUCKET_NAME_HERE`

**Why?** Terraform needs to know where to store its state file.

**How to get the bucket name:**
```bash
# Run the S3 creation command from README.md first
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
BUCKET_NAME="b4build-terraform-state-${ACCOUNT_ID}"
echo $BUCKET_NAME

# Then update the files manually or use sed:
sed -i "s/YOUR_BUCKET_NAME_HERE/$BUCKET_NAME/g" infra/shared/backend.tf
sed -i "s/YOUR_BUCKET_NAME_HERE/$BUCKET_NAME/g" infra/envs/dev/backend.tf
```

---

## ⚠️ GitHub Actions: Update OIDC Configuration

If you plan to use GitHub Actions for CI/CD, update this file:

**File:** `infra/shared/oidc.tf` - Line 32

Replace:
```hcl
"token.actions.githubusercontent.com:sub" = "repo:YOUR_GITHUB_ORG/YOUR_REPO:*"
```

With your actual GitHub org and repo:
```hcl
"token.actions.githubusercontent.com:sub" = "repo:myorg/b4build:*"
```

---

## ⚠️ Secrets: Create Before Deploying

You **MUST** create these secrets in AWS Secrets Manager before deploying the dev environment:

```bash
# OpenAI API key (required)
aws secretsmanager create-secret \
  --name b4build/dev/openai-api-key \
  --secret-string "sk-proj-YOUR_KEY_HERE" \
  --region us-east-1

# Clerk secret key (required)
aws secretsmanager create-secret \
  --name b4build/dev/clerk-secret-key \
  --secret-string "sk_YOUR_KEY_HERE" \
  --region us-east-1

# Tavily API key (required)
aws secretsmanager create-secret \
  --name b4build/dev/tavily-api-key \
  --secret-string "tvly-YOUR_KEY_HERE" \
  --region us-east-1
```

**Why?** The ECS task definition references these secrets. If they don't exist, the task will fail to start.

---

## ✅ Prerequisites Checklist

Before running Terraform, verify:

- [ ] AWS CLI installed and configured (`aws configure`)
- [ ] Terraform installed (>= 1.6)
- [ ] Docker installed (for building backend image)
- [ ] AWS credentials have admin permissions
- [ ] S3 bucket created for Terraform state
- [ ] DynamoDB table created for state locking
- [ ] Backend config files updated with bucket name
- [ ] Secrets created in Secrets Manager
- [ ] GitHub OIDC config updated (if using CI/CD)

---

## 📋 Deployment Order

**IMPORTANT:** Follow this exact order:

1. ✅ Create S3 bucket + DynamoDB table (one-time)
2. ✅ Update `backend.tf` files with bucket name
3. ✅ Create secrets in Secrets Manager
4. ✅ Deploy shared resources (`infra/shared`)
5. ✅ Deploy dev environment (`infra/envs/dev`)
6. ✅ Build & push Docker image to ECR
7. ✅ Deploy backend to ECS
8. ✅ Test health endpoint
9. ✅ Deploy frontend

**Do NOT skip steps or change the order!**

---

## 💰 Cost Warning

This infrastructure will cost approximately:
- **$4/day** (~$122/month) if left running
- **NAT Gateway alone:** $32/month

**To minimize costs:**
- Destroy infrastructure when not in use: `terraform destroy`
- Use `t4g.micro` instances (already configured)
- Enable S3 lifecycle policies (already configured)

---

## 🔒 Security Notes

### What's Secure
✅ Private subnets for backend (no public IP)
✅ Secrets in Secrets Manager (not hardcoded)
✅ IAM roles (no access keys)
✅ Encryption at rest + in transit
✅ WAF with OWASP rules
✅ Security groups with least privilege

### What's NOT Production-Ready (for grading only)
⚠️ Single NAT Gateway (not HA)
⚠️ No custom domain (using ALB DNS)
⚠️ HTTP only (no HTTPS certificate)
⚠️ Redis without auth (transit encryption disabled)
⚠️ No CloudTrail (audit logs)

**For production, you'd add:**
- Multi-NAT Gateway (one per AZ)
- Route 53 + ACM for custom domain
- HTTPS on ALB
- Redis AUTH token
- CloudTrail + Config + GuardDuty

---

## 🐛 Common Issues

### Issue: "Error creating S3 bucket: BucketAlreadyExists"
**Solution:** S3 bucket names are globally unique. Change the bucket name in the creation command.

### Issue: "Error: Secret not found"
**Solution:** Create the secrets in Secrets Manager before running `terraform apply` on dev environment.

### Issue: "Error: Backend configuration changed"
**Solution:** Run `terraform init -reconfigure` to update the backend config.

### Issue: "ECS tasks not starting"
**Solution:** Check CloudWatch Logs: `aws logs tail /ecs/b4build-dev --follow`

### Issue: "Health checks failing"
**Solution:** Verify the backend container is listening on port 8000 and `/health` endpoint exists.

### Issue: "Terraform state locked"
**Solution:** Wait for other operations to complete, or force unlock: `terraform force-unlock [LOCK_ID]`

---

## 📚 Documentation Files

- **README.md** - Main documentation (start here)
- **QUICK_START.md** - 10-command deployment
- **BEFORE_YOU_START.md** - This file (read first!)
- **ARCHITECTURE.md** - Detailed architecture
- **GRADING_CHECKLIST.md** - Verification for grading
- **SUMMARY.md** - Quick overview

**Recommended reading order:**
1. BEFORE_YOU_START.md (this file)
2. README.md
3. QUICK_START.md
4. ARCHITECTURE.md (for deep dive)

---

## 🚀 Quick Commands

```bash
# Verify AWS credentials
aws sts get-caller-identity

# Check Terraform version
terraform --version

# Format Terraform files
cd infra && terraform fmt -recursive

# Validate configuration
cd infra/envs/dev && terraform validate

# Plan changes
terraform plan

# Apply changes
terraform apply

# View outputs
terraform output

# Destroy everything
terraform destroy
```

---

## 📞 Getting Help

If you encounter issues:

1. **Check CloudWatch Logs**
   ```bash
   aws logs tail /ecs/b4build-dev --follow
   ```

2. **Check ECS task status**
   ```bash
   aws ecs describe-tasks --cluster b4build-dev --tasks [TASK_ID]
   ```

3. **Check Terraform state**
   ```bash
   terraform show
   ```

4. **Check security group rules**
   ```bash
   aws ec2 describe-security-groups --filters "Name=tag:Project,Values=b4build"
   ```

5. **Review this documentation** - Most issues are covered in README.md

---

## ✅ Ready to Deploy?

If you've completed the checklist above, you're ready to deploy!

**Start here:**
```bash
cd infra
cat README.md  # Read the full deployment guide
```

Good luck! 🎉
