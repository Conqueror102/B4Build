# Architecture (high level)

```mermaid
flowchart TB
  B[Users]
  Amp[Amplify_Next]
  subgraph public [Public_subnets]
    NAT[NAT_Gateway]
    ALB[ALB]
    WAF[WAFv2_regional]
  end
  subgraph private [Private_subnets]
    ECS[ECS_Fargate]
    RDS[RDS_Postgres_single_AZ]
    R[Redis]
  end
  B --> Amp
  B -->|API_traffic| WAF
  WAF --> ALB
  ALB --> ECS
  ECS --> RDS
  ECS --> R
  ECS --> NAT
  NAT --> Internet[Internet_egress]
```

- **Egress:** Private workloads use a **single NAT Gateway** (cost control) in the VPC module, not a NAT instance.
- **UI:** **Amplify** serves the **Next.js** `frontend/`. `NEXT_PUBLIC_API_URL` points the browser to the public **ALB** (HTTP or HTTPS) for the FastAPI API.
- **API ingress:** Browser/API clients hit **WAF** (regional) → **ALB** → Fargate in private subnets.
- **Data:** **RDS** and **Redis** only allow the **Fargate security group** on database ports; **S3** is private (task role for object access).
- **Secrets:** API keys and `DATABASE_URL` are in **Secrets Manager** and mounted via ECS `secrets` (not plaintext in the task definition for those values).

For bootstrap order (S3 state before `init`), see [README.md](README.md).
