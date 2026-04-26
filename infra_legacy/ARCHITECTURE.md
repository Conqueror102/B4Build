# B4Build AWS Architecture

## Overview

Production-grade AWS infrastructure for the AI Build Advisor platform, featuring high availability, security, scalability, and comprehensive monitoring.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                            Internet                                  │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                ┌────────────▼────────────┐
                │   CloudFront CDN        │
                │   (Edge Locations)      │
                │   + WAF Protection      │
                └────────────┬────────────┘
                             │
                ┌────────────▼────────────┐
                │  Application Load       │
                │  Balancer (ALB)         │
                │  Public Subnets (2 AZs) │
                └────────────┬────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼────┐          ┌────▼────┐         ┌────▼────┐
   │ Fargate │          │ Fargate │         │ Fargate │
   │  Task   │          │  Task   │         │  Task   │
   │   #1    │          │   #2    │         │   #3    │
   └────┬────┘          └────┬────┘         └────┬────┘
        │                    │                    │
        │         Private Subnets (2 AZs)        │
        └────────────────────┼────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
   ┌────▼────────┐     ┌─────▼──────┐      ┌─────▼─────┐
   │    RDS      │     │ElastiCache │      │    S3     │
   │  Postgres   │     │   Redis    │      │   PDFs    │
   │  Multi-AZ   │     │            │      │           │
   └─────────────┘     └────────────┘      └───────────┘
        │
        │ (Outbound to OpenAI API)
        │
   ┌────▼────────┐
   │    NAT      │
   │  Gateway    │
   └────┬────────┘
        │
   ┌────▼────────┐
   │  Internet   │
   │   Gateway   │
   └─────────────┘
```

## Network Architecture

### VPC Configuration
- **CIDR Block:** `10.0.0.0/16`
- **Availability Zones:** 2 (us-east-1a, us-east-1b)
- **DNS:** Enabled

### Subnets

#### Public Subnets (2)
- **CIDR:** `10.0.1.0/24`, `10.0.2.0/24`
- **Purpose:** ALB, NAT Gateway
- **Internet Access:** Via Internet Gateway
- **Resources:**
  - Application Load Balancer
  - NAT Gateway

#### Private Subnets (2)
- **CIDR:** `10.0.11.0/24`, `10.0.12.0/24`
- **Purpose:** Fargate, RDS, Redis
- **Internet Access:** Via NAT Gateway (outbound only)
- **Resources:**
  - ECS Fargate tasks
  - RDS Postgres
  - ElastiCache Redis

### Routing

#### Public Route Table
```
Destination     Target
10.0.0.0/16     local
0.0.0.0/0       igw-xxxxx (Internet Gateway)
```

#### Private Route Table
```
Destination     Target
10.0.0.0/16     local
0.0.0.0/0       nat-xxxxx (NAT Gateway)
```

## Compute Layer

### ECS Fargate
- **Cluster:** `b4build-dev`
- **Service:** `b4build-backend`
- **Launch Type:** Fargate (serverless)
- **Task Definition:**
  - CPU: 512 (0.5 vCPU)
  - Memory: 1024 MB
  - Container: Python 3.12 + FastAPI + LangGraph

### Auto-Scaling
- **Min Tasks:** 1
- **Max Tasks:** 4
- **Scale Out:** CPU > 70% or Memory > 80%
- **Scale In:** CPU < 50% and Memory < 60%
- **Cooldown:** 60s (scale out), 300s (scale in)

### Container Configuration
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Data Layer

### RDS Postgres
- **Engine:** PostgreSQL 16.3
- **Instance Class:** db.t4g.micro (ARM-based)
- **Storage:** 20 GB GP3 (auto-scaling to 100 GB)
- **Multi-AZ:** Enabled (automatic failover)
- **Backups:** 7 days retention
- **Encryption:** At rest (default KMS)
- **Performance Insights:** Enabled (7 days)

### ElastiCache Redis
- **Engine:** Redis 7.1
- **Node Type:** cache.t4g.micro (ARM-based)
- **Nodes:** 1 (single-node for dev)
- **Encryption:** At rest enabled
- **Use Cases:**
  - Session caching
  - Rate limiting
  - LangGraph checkpoints

### S3
- **Bucket:** `b4build-dev-pdfs-[account-id]`
- **Purpose:** PDF exports
- **Versioning:** Enabled
- **Encryption:** AES256
- **Lifecycle:** Delete after 30 days
- **Access:** Via CloudFront (OAI)

## Load Balancing

### Application Load Balancer
- **Type:** Application (Layer 7)
- **Scheme:** Internet-facing
- **Subnets:** Public subnets (2 AZs)
- **Listeners:**
  - HTTP (80) → Forward to Fargate
  - HTTPS (443) → Not configured (no domain)

### Target Group
- **Type:** IP (for Fargate)
- **Protocol:** HTTP
- **Port:** 8000
- **Health Check:**
  - Path: `/health`
  - Interval: 30s
  - Timeout: 5s
  - Healthy threshold: 2
  - Unhealthy threshold: 3

## Content Delivery

### CloudFront
- **Purpose:** CDN for S3 PDFs
- **Origin:** S3 bucket (via OAI)
- **Price Class:** PriceClass_100 (US, Canada, Europe)
- **Cache Behavior:**
  - TTL: 1 hour (default)
  - Compression: Enabled
  - HTTPS: Redirect HTTP to HTTPS

### Origin Access Identity (OAI)
- Restricts S3 access to CloudFront only
- No direct S3 public access

## Security

### WAF (Web Application Firewall)
- **Attached to:** ALB
- **Rules:**
  1. **AWS Managed - Core Rule Set** (OWASP Top 10)
  2. **AWS Managed - Known Bad Inputs**
  3. **AWS Managed - SQL Injection**
  4. **Custom - Rate Limiting** (2000 req/5min per IP)

### Security Groups

#### ALB Security Group
```
Inbound:
  - Port 80 (HTTP) from 0.0.0.0/0
  - Port 443 (HTTPS) from 0.0.0.0/0
Outbound:
  - All traffic to 0.0.0.0/0
```

#### Fargate Security Group
```
Inbound:
  - Port 8000 from ALB Security Group
Outbound:
  - All traffic to 0.0.0.0/0
```

#### RDS Security Group
```
Inbound:
  - Port 5432 from Fargate Security Group
Outbound:
  - None
```

#### Redis Security Group
```
Inbound:
  - Port 6379 from Fargate Security Group
Outbound:
  - None
```

### IAM Roles

#### ECS Task Execution Role
- **Purpose:** Pull images, write logs, read secrets
- **Policies:**
  - `AmazonECSTaskExecutionRolePolicy`
  - Custom: Secrets Manager read access

#### ECS Task Role
- **Purpose:** Application permissions
- **Policies:**
  - Custom: S3 read/write for PDFs

#### GitHub Actions Role
- **Purpose:** CI/CD deployments
- **Authentication:** OIDC (no long-lived keys)
- **Policies:**
  - ECR push
  - ECS update service

### Secrets Management
- **Service:** AWS Secrets Manager
- **Secrets:**
  - `b4build/dev/openai-api-key`
  - `b4build/dev/clerk-secret-key`
  - `b4build/dev/tavily-api-key`
  - `b4build/dev/db-password` (auto-generated)
- **Rotation:** Manual (can enable auto-rotation)

## Monitoring & Logging

### CloudWatch Logs
- **ECS Logs:** `/ecs/b4build-dev`
- **VPC Flow Logs:** `/aws/vpc/b4build-dev`
- **WAF Logs:** `/aws/wafv2/b4build-dev`
- **Retention:** 7 days

### CloudWatch Alarms

#### RDS Alarms
- CPU > 80% (2 periods of 5 min)
- Free storage < 2 GB

#### Redis Alarms
- CPU > 75% (2 periods of 5 min)
- Memory > 80% (2 periods of 5 min)

#### ALB Alarms
- Response time > 1s (2 periods of 5 min)
- Unhealthy targets > 0 (2 periods of 1 min)

#### CloudFront Alarms
- 5xx error rate > 5% (2 periods of 5 min)

#### WAF Alarms
- Blocked requests > 100 (2 periods of 5 min)

### Container Insights
- **Enabled:** Yes
- **Metrics:**
  - CPU utilization
  - Memory utilization
  - Network I/O
  - Task count

### Performance Insights
- **Enabled:** Yes (RDS)
- **Retention:** 7 days
- **Metrics:**
  - Top SQL queries
  - Wait events
  - Database load

## Disaster Recovery

### Backups

#### RDS
- **Automated Backups:** Enabled
- **Retention:** 7 days
- **Backup Window:** 03:00-04:00 UTC
- **Maintenance Window:** Monday 04:00-05:00 UTC

#### S3
- **Versioning:** Enabled
- **Lifecycle:** Delete after 30 days
- **Cross-Region Replication:** Not configured

### High Availability

#### Multi-AZ Deployment
- **RDS:** Automatic failover to standby
- **ALB:** Distributes across 2 AZs
- **Fargate:** Tasks spread across AZs

#### Recovery Time Objective (RTO)
- **RDS Failover:** ~60 seconds
- **ECS Task Restart:** ~30 seconds
- **ALB Health Check:** ~90 seconds

#### Recovery Point Objective (RPO)
- **RDS:** ~5 minutes (automated backups)
- **S3:** 0 (versioning enabled)

## Cost Optimization

### Instance Types
- **RDS:** db.t4g.micro (ARM, 20% cheaper)
- **Redis:** cache.t4g.micro (ARM, 20% cheaper)
- **Fargate:** 0.5 vCPU / 1 GB (right-sized)

### Storage
- **RDS:** GP3 (cheaper than GP2)
- **S3:** Lifecycle policy (delete old PDFs)

### Network
- **NAT Gateway:** Single instance (not HA)
- **CloudFront:** PriceClass_100 (cheapest)

### Cost Breakdown (Monthly)
```
Service                 Cost/Month
─────────────────────────────────
Fargate (1 task)        $15.00
ALB                     $18.00
RDS (Multi-AZ)          $30.00
ElastiCache             $12.00
NAT Gateway             $32.00
CloudFront              $3.00
WAF                     $6.00
S3 + Secrets + Logs     $6.00
─────────────────────────────────
Total                   $122.00
```

## Scalability

### Horizontal Scaling
- **ECS:** Auto-scales 1-4 tasks
- **RDS:** Read replicas (not configured)
- **Redis:** Cluster mode (not configured)

### Vertical Scaling
- **RDS:** Can upgrade instance class
- **Fargate:** Can increase CPU/memory
- **Redis:** Can upgrade node type

### Performance Limits
- **ALB:** 25 new connections/sec per target
- **Fargate:** 4 tasks max (configurable)
- **RDS:** ~100 connections (t4g.micro)
- **Redis:** ~10,000 ops/sec (t4g.micro)

## Compliance & Best Practices

### Security Best Practices
✅ Private subnets for backend
✅ Least-privilege security groups
✅ Secrets Manager (no hardcoded credentials)
✅ IAM roles (no access keys)
✅ Encryption at rest + in transit
✅ WAF with OWASP rules
✅ VPC Flow Logs

### High Availability Best Practices
✅ Multi-AZ deployment
✅ Auto-scaling
✅ Health checks
✅ Automated backups
✅ Load balancing

### Operational Best Practices
✅ Infrastructure as Code (Terraform)
✅ CloudWatch monitoring
✅ Automated deployments (GitHub Actions)
✅ Structured logging
✅ Performance metrics

## Future Enhancements

### Phase 2 (Production)
- [ ] Custom domain (Route 53 + ACM)
- [ ] HTTPS on ALB
- [ ] RDS read replicas
- [ ] Redis cluster mode
- [ ] Multi-region deployment

### Phase 3 (Scale)
- [ ] Aurora Serverless (instead of RDS)
- [ ] DynamoDB (for high-throughput data)
- [ ] Lambda (for async tasks)
- [ ] SQS (for job queues)
- [ ] Step Functions (for workflows)

### Phase 4 (Enterprise)
- [ ] AWS Config (compliance)
- [ ] GuardDuty (threat detection)
- [ ] CloudTrail (audit logs)
- [ ] AWS Backup (centralized backups)
- [ ] AWS Organizations (multi-account)

## References

- [AWS Well-Architected Framework](https://aws.amazon.com/architecture/well-architected/)
- [ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)
- [RDS Best Practices](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/CHAP_BestPractices.html)
- [WAF Best Practices](https://docs.aws.amazon.com/waf/latest/developerguide/waf-chapter.html)
