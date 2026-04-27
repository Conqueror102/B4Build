# B4Build / AI Build Advisor — AWS infrastructure (Terraform)

**Hands-on runbook (WSL, copy-paste commands, in order):** [docs/SETUP_GUIDE.md](../docs/SETUP_GUIDE.md) — use that file first; this `README` is for stack detail.

**CI:** Set GitHub **secret** `AWS_ROLE_ARN` = `github_actions_role_arn` from `shared` output. For **pinning the ECS image to the git commit SHA** in `deploy-backend.yml`, set **`cicd_terraform_state_s3_bucket`** in **`shared/terraform.tfvars`**, re-apply **shared**, and add a GitHub **Actions variable** **`CICD_TERRAFORM_STATE_S3_BUCKET`** (same name as the state bucket). See `infra/shared/cicd_github_iam.tf` and the setup guide.

Greenfield stack: **no Route 53** (add ACM validation CNAMEs at your **registrar** or Cloudflare), **NAT Gateway** via `terraform-aws-modules/vpc`, **RDS** module, **ALB + WAFv2 + ACM**, **ECS Fargate** with **Secrets Manager** `secrets:` on the task definition, **ElastiCache Redis**, private **S3** for PDFs, **ECR** + **GitHub OIDC** in `shared/`, **AWS Amplify** (Next.js `WEB_COMPUTE` with app root `frontend/`) in `envs/dev`.

## Path-based GitHub Actions

Pushes/PRs only run workflows whose **`paths` filters** match, so a **frontend-only** change does not trigger `deploy-backend`, backend CI, or `terraform` (and the reverse is true for backend/infra). See the `on: paths` blocks in [`.github/workflows`](../.github/workflows/).

| Workflow                | Fires on changes under |
|------------------------|------------------------|
| `ci-backend.yml`        | `backend/**`            |
| `ci-frontend.yml`       | `frontend/**`           |
| `deploy-backend.yml`      | `backend/**` (push to `main`) |
| `terraform.yml`         | `infra/**` (plan/apply) |

`NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` and `CLERK_SECRET_KEY` in **GitHub → Settings → Secrets** are only needed if **Frontend CI**’s `pnpm run build` fails (use Clerk *test* keys in non-prod).

**Amplify** is not path-aware like Actions: a push to a connected branch still **starts a build** unless you use AWS **monorepo** settings (app root `frontend/`) and/or a separate process. GHA and Amplify are independent.

## Do not run `terraform init` until the S3 remote state bucket exists

If `backend "s3"` is configured, **`terraform init` will fail** until the bucket (and optional DynamoDB lock table) is created and the **bucket name** in `shared/backend.tf` and `envs/dev/backend.tf` is updated from `YOUR_BUCKET_NAME_HERE`.

**Order:**

1. **One-time (AWS CLI or Console):** create the state bucket, versioning, encryption, public access block, and DynamoDB table `b4build-terraform-lock` (see commands below).
2. **Edit** `infra/shared/backend.tf` and `infra/envs/dev/backend.tf` — set `bucket = "your-actual-bucket-name"`.
3. **Now** run `terraform init` in `infra/shared`, then `terraform apply` (or use `-backend-config` if you use partial config).
4. **Then** `cd infra/envs/dev`, `terraform init`, `terraform apply`.
5. **GitHub:** set repository secret `AWS_ROLE_ARN` to the `github_actions_role_arn` output from `shared` (after you set `github_org` / `github_repo` in `shared/terraform.tfvars`).

## Why NAT Gateway (for reviewers / grading)

**NAT Gateway** is a **managed** service in a **public** subnet. **Private** subnets (Fargate, RDS) send **outbound** internet traffic through it (ECR image pulls, Secrets Manager, third-party APIs). It costs more in steady state than a self-managed **NAT instance**, but you **do not** operate EC2 for NAT, and it matches the standard `terraform-aws-modules/vpc` pattern (`enable_nat_gateway = true`, `single_nat_gateway = true` to limit cost to one gateway).

## Manual bootstrap: S3 + DynamoDB for Terraform state

```bash
export REGION=us-east-1
export BUCKET="b4build-terraform-state-$(aws sts get-caller-identity --query Account --output text)"

aws s3api create-bucket --bucket "$BUCKET" --region "$REGION"  # add LocationConstraint if not us-east-1
aws s3api put-bucket-versioning --bucket "$BUCKET" --versioning-configuration Status=Enabled
# ... encryption + public access block (see your org policy)
aws dynamodb create-table --table-name b4build-terraform-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST --region "$REGION"
```

After that, put `$BUCKET` into both `backend` blocks, **then** run `terraform init`.

## Layout

| Path | Role |
|------|------|
| `shared/` | Remote state, **ECR** `b4build/backend`, **GitHub OIDC** deploy role (ECR + ECS) |
| `envs/dev/` | VPC, NAT GW, ALB+WAF+ACM, RDS Postgres, Redis, S3, secrets, ECS, migrations task, **Amplify app** |

## ACM (HTTPS) without Route 53

1. Set `api_fqdn` in `envs/dev/terraform.tfvars` (e.g. `api.example.com`).
2. `terraform apply` and read **`acm_validation_records` output** — add those **CNAME** records at your **DNS host** (registrar, Cloudflare), **not** in AWS Route 53.
3. When the certificate is **ISSUED** in the ACM console, set `enable_https_listener = true` and apply again to create the **443** listener on the ALB.
4. Until then, the ALB uses **HTTP on 80** (fine for bring-up; lock down in production with HTTPS as above).

## App environment variables (backend `Settings`)

Your Python app ([`backend/src/settings.py`](../backend/src/settings.py)) reads **Pydantic** settings from the environment. Names are the usual UPPER_SNAKE of the field (`app_env` → `APP_ENV`, `database_url` → `DATABASE_URL`).

| In AWS (ECS task) | Source |
|-------------------|--------|
| `APP_ENV` | Terraform `var.app_env` (default `staging`) — use `development` / `staging` / `production` to match `Settings` |
| `REDIS_URL` | Injected in task definition (Redis cluster address) |
| `S3_BUCKET_NAME` | Injected (for future PDFs; not yet a `Settings` field — **harmless**, or add to `Settings` if you use it) |
| `AWS_DEFAULT_REGION` | Region string |
| `LANGCHAIN_TRACING_V2`, `LANGCHAIN_PROJECT` | Plain env on the task (`true` and `{project}-{env}`, e.g. `b4build-dev`) for LangSmith |
| `OPENAI_API_KEY`, `TAVILY_API_KEY`, `CLERK_SECRET_KEY`, `SENTRY_DSN`, `LANGCHAIN_API_KEY`, `DATABASE_URL` | **Secrets Manager** `secrets` → mounted as env vars. `DATABASE_URL` is `postgresql://...`; the app rewrites to `postgresql+asyncpg://` in code. LangSmith API key lives in `langsmith-api-key`. |

Locally, use a **`backend/.env`** (or project `.env` per `Settings`) with the same variable names. For the **Next.js** app, use variables prefixed with `NEXT_PUBLIC_*` only for values that are safe in the browser (e.g. Clerk publishable key, public API base URL) — not secret keys.

## Amplify (frontend) — one path

Terraform **only** creates the Amplify **app**: `NEXT_PUBLIC_API_URL` → your **ALB**, optional `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` from `terraform.tfvars`, and a **build spec** (same as [`amplify.yml`](../amplify.yml) in the monorepo root — keep that file in git).

**When your GitHub repo exists:** in **AWS Console → Amplify → your app → Connect branch** → pick the repo and `main` (OAuth; nothing to paste into Terraform). Pushes to `main` will build from `frontend/` using the root `amplify.yml`.

After the ALB has **HTTPS**, update `NEXT_PUBLIC_API_URL` in the Amplify app to `https://…` (console or a small Terraform change).

Outputs: `amplify_app_id`, `amplify_default_domain`.

## After apply

- Push a backend image to ECR (`:latest` and/or CI tag).
- Replace **placeholder** secret values in Secrets Manager (`openai`, `tavily`, `clerk`, `sentry`, `langsmith-api-key`)—Terraform created versions with `REPLACE_...` and `lifecycle ignore_changes` on values.
- Run **migrations** with `aws ecs run-task` (see `envs/dev` outputs: `migrations_run_command` / subnets).
- **Frontend:** push code (including root [`amplify.yml`](../amplify.yml)), then in Amplify **connect the branch** and wait for a green build. Set `NEXT_PUBLIC_API_URL` to `https` when the API uses HTTPS.

## Validation (after backend bucket exists and `init` is configured)

```bash
terraform fmt -recursive .
cd infra/shared && terraform validate
cd ../envs/dev && terraform validate
```

## Legacy

The previous tree is under **`../infra_legacy/`** (kept for reference, not used by the new `infra/`).
