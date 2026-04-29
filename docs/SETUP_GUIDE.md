# Setup runbook — WSL (Ubuntu) + AWS + Terraform + GitHub

Use **Windows Subsystem for Linux (Ubuntu)** for every shell command in this doc. **PowerShell / CMD** paths and quoting differ; in WSL your project is often:

`/mnt/c/Users/YourName/Desktop/Ai advisor` — **cd there first** (quotes matter if the path has spaces):

```bash
cd "/mnt/c/Users/YourName/Desktop/Ai advisor"
```

Replace `YourName` and fix the path if your folder lives somewhere else. All `bash` below assumes you are in the **repository root** (the folder that contains `backend/`, `frontend/`, `infra/`).

---

## How to read this doc

- **“Why”** = one sentence so you are not lost.
- **“Run”** = copy into WSL, press Enter, read any errors.
- **Order matters**: do the parts in order. Skip only sections marked *optional*.

End goal: **Terraform** creates your AWS **network, database, load balancer, ECS, ECR, Amplify**; the **API** runs in **Docker** on **ECS**; the **web app** is built in **GitHub/Amplify**; **secrets** live in **AWS Secrets Manager**.

---

## What you need installed (WSL)

| You need | Check / install |
|----------|-----------------|
| WSL2 + Ubuntu | Microsoft Store, or `wsl --install` in an admin Windows terminal. |
| **AWS CLI v2 (Linux)** | [Install for Linux](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) *inside* WSL, not the Windows .msi. Then `aws --version`. |
| **Terraform** ≥ 1.6 | [HashiCorp install](https://developer.hashicorp.com/terraform/install) in WSL. Then `terraform version`. |
| **Git** | `sudo apt update && sudo apt install -y git` then `git --version`. |
| **Docker** (optional; for local image builds) | [Docker in WSL](https://docs.docker.com/desktop/wsl/) — or skip and use only GitHub to build. |

**Log in to AWS from WSL** — the CLI only works after it knows *who* you are. You need **one** of these, depending on your account (not both).

**A — Your own / lab account: IAM user access key (most common for a first-time setup)**  
1. In a browser, open the **AWS Console** → sign in.  
2. Go to **IAM** → **Users** → select **your** user (or **Create user** with a name like `terraform-local`, then attach a policy that can create the resources in this project — in a throwaway **dev** account, **AdministratorAccess** is the simplest for learning; tighten later).  
3. Open that user → tab **Security credentials** → **Create access key** → choose **Command Line Interface (CLI)** → create.  
4. Copy the **Access key** and **Secret access key** (the secret is shown **once**).  
5. In WSL:

```bash
aws configure
# AWS Access Key ID:     ← paste the access key
# AWS Secret Access Key:  ← paste the secret
# Default region:         us-east-1   (or the region you will use)
# Default output format:  json
```

Do **not** create keys for the **root** user; use a normal IAM user.

**B — Work / school account: AWS IAM Identity Center (SSO)**  
Use this only if your org already set up **single sign-on** to AWS. Your admin gives you a **portal URL** and maybe an **SSO start URL** / **account id**. In WSL:

```bash
aws configure sso
# Answer the prompts (SSO start URL, region, account, role name — from your org)
```

SSO gives you a **profile name**. In **every** new WSL session before `terraform` / `aws`:

```bash
export AWS_PROFILE=the-name-sso-showed-you
# optional: add that line to ~/.bashrc so you do not forget
```

**Prove the CLI is logged in (either A or B):**

```bash
aws sts get-caller-identity
```

You should see `Account` and `Arn`. If you get an error, stop and fix auth before Terraform.

---

## Part 1 — What happens in one paragraph

1. You create an **S3 bucket** (and a **DynamoDB** lock table) so **Terraform’s state** is not only on your laptop.  
2. You put that **bucket name** in two `backend.tf` files so **shared** and **dev** Terraform can run.  
3. You run **`terraform apply` in `infra/shared`** → creates **ECR** and a **GitHub OIDC** IAM role (CI can act in AWS without long‑lived keys).  
4. You add **one GitHub secret** and **one variable** (optional but recommended) so **Actions** can log in.  
5. You run **`terraform apply` in `infra/envs/dev`** → **VPC, ALB, RDS, ECS, Amplify**, etc.  
6. You fill in **real API keys** in **Secrets Manager**, then **push the backend** so the **container** runs, then connect **Amplify** to the repo for the **frontend**.

---

## Part 2 — Create the state bucket and lock table (one time)

**Why:** Terraform is configured to store state in **S3** and to lock with **DynamoDB** so two applies never corrupt each other.

**Set region and account** (use your real region, often `us-east-1`):

```bash
export AWS_REGION="us-east-1"
export ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
echo "Account: $ACCOUNT_ID"
```

**Create the S3 bucket** (name includes your account so it is unique):

```bash
export BUCKET="b4build-terraform-state-${ACCOUNT_ID}"
echo "Bucket will be: $BUCKET"
```

`us-east-1` (no `LocationConstraint`):

```bash
if [ "$AWS_REGION" = "us-east-1" ]; then
  aws s3api create-bucket --bucket "$BUCKET" --region us-east-1
else
  aws s3api create-bucket --bucket "$BUCKET" --region "$AWS_REGION" \
    --create-bucket-configuration "LocationConstraint=${AWS_REGION}"
fi
```

**Turn on versioning** (required for state safety):

```bash
aws s3api put-bucket-versioning \
  --bucket "$BUCKET" \
  --versioning-configuration Status=Enabled
```

**Create the lock table** (name must match what is in your `backend.tf` files, default in this repo is `b4build-terraform-lock`):

```bash
aws dynamodb create-table \
  --table-name b4build-terraform-lock \
  --attribute-definitions AttributeName=LockID,AttributeType=S \
  --key-schema AttributeName=LockID,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST \
  --region "$AWS_REGION"
```

**Write down** the value of **`$BUCKET`** (you will paste it twice in Part 3).

*Optional: in the AWS web console, open S3 → your bucket → set default encryption and “Block all public access” (recommended).*

---

## Part 3 — Point Terraform at the bucket (edit two files)

**Why:** Until the bucket name is in the `backend` blocks, `terraform init` cannot load remote state.

1. Open **`infra/shared/backend.tf`**.  
2. Find the line with `bucket = "YOUR_BUCKET_NAME_HERE"` and replace the string with your **real** bucket name (same as `$BUCKET` above, no `export`, just the name, e.g. `b4build-terraform-state-123456789012`).  
3. Do the same in **`infra/envs/dev/backend.tf`**.

**Do not run** `terraform init` until both files are saved.

---

## Part 4 — `terraform.tfvars` for **shared** and **dev**

**Why:** These files pass non-secret **settings** (region, GitHub `org`/`repo`, ECR name). They are **not** committed with secrets; copy from the `*.example` files.

**From the repo root in WSL:**

```bash
cd "/path/to/Ai advisor"   # your real path

cp infra/shared/terraform.tfvars.example infra/shared/terraform.tfvars
cp infra/envs/dev/terraform.tfvars.example infra/envs/dev/terraform.tfvars
```

**Edit** `infra/shared/terraform.tfvars` in your editor. Minimum you must set:

- `github_org` — your GitHub **username** or **organization** (exactly as in the URL, case-sensitive).  
- `github_repo` — **only** the repo name (e.g. `ai-build-advisor`), not the full URL.

**To pin ECS images to git SHAs in GitHub Actions later** (recommended once you are comfortable), also set in the same file (same name as the bucket in Part 2):

```hcl
cicd_terraform_state_s3_bucket = "b4build-terraform-state-123456789012"
# leave the default for cicd_attach_terraform_admin_policy unless you have a reason to turn it off
```

**Edit** `infra/envs/dev/terraform.tfvars`: at least set `app_env` if the default is wrong for you (`development`, `staging`, or `production` to match the Python `Settings` in the backend). Leave `ecr_image_tag` alone for now; CI can set it to the **git commit** later.

---

## Part 5 — Run Terraform: **`infra/shared`**

**Why:** Creates the **ECR** repository and the **GitHub OIDC** IAM role used by `AWS_ROLE_ARN` in Actions.

```bash
cd "/path/to/Ai advisor/infra/shared"
terraform init
terraform plan
terraform apply
```

**Copy the output ARN** (you will paste it into GitHub in Part 6):

```bash
terraform output -raw github_actions_role_arn
```

**Example output:** `arn:aws:iam::123456789012:role/b4build-github-actions-deploy`

If `apply` fails, read the error (often wrong `github_org`/`github_repo` or wrong AWS account permissions).

---

## Part 6 — GitHub: secret, variable, push

**Why:** Workflows in `.github/workflows/` use **OIDC** — the repo has **no** AWS static keys, only a role ARN and optional settings.

1. On GitHub: your repo → **Settings** → **Secrets and variables** → **Actions**.  
2. **New repository secret**  
   - **Name:** `AWS_ROLE_ARN`  
   - **Value:** paste the `terraform output` ARN from Part 5 (full line, no spaces).  
3. **Variables** (same page, tab “Variables”): **New variable**  
   - **Name:** `CICD_TERRAFORM_STATE_S3_BUCKET`  
   - **Value:** the **same** S3 bucket name you put in `cicd_terraform_state_s3_bucket` in **shared** `tfvars` and in both `backend.tf` files.  
   - *If you did not set `cicd_terraform_state_s3_bucket` yet, you can add this later;* then `deploy-backend` will only do a simple ECS rollout without pinning the task definition in Terraform.  

4. **Push** this project to the **same** `org/repo` you set in `terraform.tfvars` (e.g. create an empty repo on GitHub, add `origin`, `git push -u origin main`).

**Rule:** the strings **`github_org`** and **`github_repo` in `infra/shared/terraform.tfvars`** must match the GitHub repo. If the repo is `https://github.com/acme/ai-app`, then `github_org = "acme"` and `github_repo = "ai-app"`.

---

## Part 7 — Run Terraform: **`infra/envs/dev`**

**Why:** Creates the **main stack** (VPC, load balancer, database, ECS, secrets placeholders, etc.). **Takes a long time** the first time.

**Prerequisites:** ECR from **Part 5** must exist; `ecr_repository_name` in `dev` `tfvars` should match the ECR name from **shared** (default `b4build/backend`).

```bash
cd "/path/to/Ai advisor/infra/envs/dev"
terraform init
terraform plan
terraform apply
```

**Useful outputs** (run after apply):

```bash
terraform output alb_http_url
terraform output alb_dns_name
terraform output cloudfront_url
terraform output next_public_api_url
terraform output -json acm_validation_records
```

Save **`next_public_api_url`** (or **`cloudfront_url`**): this is what **`NEXT_PUBLIC_API_URL`** should be for Amplify — by default the **CloudFront** HTTPS URL so the browser does not block API calls as mixed content. The bare **`alb_http_url`** is only for direct curl testing or local debugging, not for a public HTTPS frontend.

---

## Part 8a — HTTPS without a domain (default: CloudFront)

**Why:** An HTTPS Amplify page cannot call `http://...elb.amazonaws.com` (mixed content). Terraform creates **CloudFront** in front of the ALB by default (`create_cloudfront = true`), giving a free **`https://dxxx.cloudfront.net`** URL.

1. In `infra/envs/dev/terraform.tfvars` set **`cors_allow_origins`** to a JSON-style list containing your Amplify page origin, e.g. `cors_allow_origins = ["https://main.xxxxx.amplifyapp.com"]`.  
2. `terraform apply` in `infra/envs/dev`.  
3. Read `terraform output next_public_api_url` — Terraform already wires this into the Amplify app’s **`NEXT_PUBLIC_API_URL`**.  
4. **Redeploy** the Amplify frontend so the new URL is baked into the bundle.  
5. Test: `curl "$(terraform output -raw cloudfront_url)/health"` should return healthy.

## Part 8b — HTTPS with your own domain on the ALB (optional)

**Why:** You want `https://api.yourdomain.com` directly on the ALB instead of (or in addition to) CloudFront. This stack does **not** use Route 53: you add **CNAMEs** for ACM at your **registrar** or **Cloudflare**.

1. In `infra/envs/dev/terraform.tfvars` set, for example, `api_fqdn = "api.example.com"`.  
2. Run `terraform apply` in `infra/envs/dev` again.  
3. `terraform output -json acm_validation_records` → add each **CNAME** at your DNS host.  
4. Wait for the certificate in **ACM** to be **Issued** (AWS console, same region as the ALB).  
5. Set `enable_https_listener = true` in the same `tfvars`, then `terraform apply` again.  
6. Add a **DNS A/ALIAS or CNAME** for `api.example.com` pointing to the **ALB** (from outputs / console).  
7. If you also use CloudFront, `NEXT_PUBLIC_API_URL` still prefers CloudFront unless you set `create_cloudfront = false`; then set Amplify’s **`NEXT_PUBLIC_API_URL`** to `https://api.example.com` and redeploy the frontend.

---

## Part 9 — Real secrets (not the `REPLACE_...` placeholders)

**Why:** The app will not call OpenAI, Clerk, etc. until the values in **Secrets Manager** are real.

1. AWS **Console** → **Secrets Manager** (region = your `dev` region, e.g. `us-east-1`).  
2. Find the secrets for `openai`, `tavily`, `clerk`, `sentry`, and **`langsmith-api-key`** (paths are `${project}/${env}/...` from Terraform).  
3. For each, **put a new value** (plain string for `DATABASE_URL` only if you really must override; normally Terraform already wires RDS). **LangSmith:** paste your LangSmith API key (`lsv2_...`) into `langsmith-api-key`. The ECS task definition sets **`LANGCHAIN_TRACING_V2=true`** and **`LANGCHAIN_PROJECT`** to `{project}-{env}` (e.g. `b4build-dev`).  
4. Locally, copy [`.env.example`](../.env.example) to `.env` and set **`LANGCHAIN_*`** if you want traces during development; use `./scripts/push-secrets-to-aws.sh` to sync **`LANGCHAIN_API_KEY`** to the same secret name as in AWS.  
5. In **ECS** → your service → **update** or run **`deploy-backend`** on GitHub so new tasks start (they read the latest secret version).

---

## Part 10 — First backend image (GitHub, easiest)

**Why:** ECS runs a **Docker** image from **ECR**; the workflow builds and pushes it.

- Push a commit that touches `backend/**` to **`main`**, **or** open **Actions** → **Deploy Backend to ECS** → **Run workflow**.  
- Watch the run: **ECR push**, then either **Terraform** (if `CICD_TERRAFORM_STATE_S3_BUCKET` is set) or a **rollout** only.  
- In **ECS** → service → **Tasks**, check that a new task is **running** and the load balancer’s target group is **healthy** (`/health` on port 8000).

**First manual push (WSL)** if you do not use Actions yet:

```bash
export AWS_REGION="us-east-1"
export ACCOUNT_ID="$(aws sts get-caller-identity --query Account --output text)"
# Get ECR login URL (after shared apply):
cd "/path/to/Ai advisor/infra/shared"
ECR_BASE="$(terraform output -raw ecr_repository_url)"   # registry/account/repo  no :tag
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

cd "/path/to/Ai advisor/backend"
TAG="$(git rev-parse HEAD)"   # full 40-char sha; same idea as GitHub’s commit SHA
docker build -t "${ECR_BASE}:${TAG}" .
docker tag "${ECR_BASE}:${TAG}" "${ECR_BASE}:latest"
docker push "${ECR_BASE}:${TAG}"
docker push "${ECR_BASE}:latest"

# Point the ECS task definition at this tag (so Terraform and AWS agree):
cd "/path/to/Ai advisor/infra/envs/dev"
terraform apply -lock-timeout=5m -refresh=false \
  -var="ecr_image_tag=${TAG}" \
  -target=aws_ecs_task_definition.backend \
  -target=aws_ecs_task_definition.migrations \
  -target=aws_ecs_service.backend
```

---

## Part 11 — DB migrations (one time after RDS exists)

**Why:** The database schema is applied with **Alembic**; Fargate tasks run in **private** subnets, so you usually run a **one-off** ECS **run-task** using the “migrations” task definition, or a bastion. Build the `aws ecs run-task ...` command from `terraform output migrations_run_command` and your `private_subnet_ids` in the same folder:

```bash
cd "/path/to/Ai advisor/infra/envs/dev"
terraform output -raw migrations_run_command
terraform output -json private_subnet_ids
```

Substitute two subnet IDs and the security group id from `terraform output fargate_security_group_id`.

---

## Part 12 — Amplify (frontend)

**Why:** The **browser** does not use Docker from this guide; it loads the Next app from **Amplify** and calls the API URL in `NEXT_PUBLIC_API_URL` — by default the **CloudFront** HTTPS URL from Part 8a.

1. AWS **Amplify** → your app (created by Terraform) → **Host** → **Connect** your Git branch (OAuth to GitHub).  
2. Make sure the repo’s **`amplify.yml`** matches your layout (this monorepo builds from `frontend/` at the root file).  
3. In the Amplify app, check **Environment variables** for `NEXT_PUBLIC_API_URL` = `terraform output next_public_api_url` (CloudFront by default). After any Terraform change to that value, **rebuild** Amplify.  
4. If the page loads but API calls fail with CORS errors, verify **`cors_allow_origins`** in `terraform.tfvars` includes the exact **`https://`** Amplify URL (same origin the browser shows in the address bar). Terraform passes this to ECS as **`CORS_ALLOW_ORIGINS`**.

---

## Part 13 — Develop locally (no AWS deploy)

**Backend (Python, uv):**

```bash
cd "/path/to/Ai advisor/backend"
# install uv: https://docs.astral.sh/uv/
uv sync
# copy .env or set env vars (APP_ENV, DATABASE_URL for a local DB, etc.)
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend (Node, pnpm):**

```bash
cd "/path/to/Ai advisor/frontend"
pnpm install
export NEXT_PUBLIC_API_URL="http://127.0.0.1:8000"
pnpm dev
```

---

## Quick reference — which GitHub Action runs when

| When you change… | This workflow can run (paths in `on:`) |
|------------------|----------------------------------------|
| `backend/**` | `ci-backend.yml`, `deploy-backend.yml` on `main` |
| `frontend/**` | `ci-frontend.yml` |
| `infra/**` | `terraform.yml` (PR plan, `main` apply) |

`deploy-backend` and `terraform.yml` need `AWS_ROLE_ARN`. Image **SHA pinning** in the ECS task def needs the **variable** and **shared** CICD bucket, as in Part 6.

---

## Troubleshooting (quick)

| Problem | What to do |
|--------|------------|
| `terraform init` fails, S3 error | Same bucket name in both `backend.tf` files; bucket exists in the same region. |
| GitHub: “not authorized to assume role” | `github_org` / `github_repo` in `shared/terraform.tfvars` match the repo; re-`apply` in `infra/shared`; secret `AWS_ROLE_ARN` matches latest `terraform output`. |
| Deploy workflow: AccessDenied on S3 | In `shared`, set `cicd_terraform_state_s3_bucket` and re-`apply` **shared**; set `CICD_TERRAFORM_STATE_S3_BUCKET` in GitHub. |
| Target group **unhealthy** | App must serve HTTP **200** on the path in Terraform (default `/health` on **8000**). |

---

## File cheat sheet

| File | You touch it for… |
|------|-------------------|
| `infra/shared/backend.tf` + `infra/envs/dev/backend.tf` | S3 state **bucket** name. |
| `infra/shared/terraform.tfvars` | GitHub org/repo, optional **CICD** state bucket. |
| `infra/envs/dev/terraform.tfvars` | `app_env`, `api_fqdn`, etc. |
| `backend/.dockerignore` | What **not** to send in `docker build` (optional cleanup). |
| `amplify.yml` | How **Amplify** builds `frontend/`. |
| `infra/README.md` | Deeper **architecture** notes. |

This runbook is the **hands-on path**; the older dense reference material was folded into the steps above. If something fails, copy the **exact** error from WSL and the **last** command you ran; that is enough to debug the next problem.
