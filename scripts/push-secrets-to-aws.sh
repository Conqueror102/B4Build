#!/usr/bin/env bash
# Push app secrets from a local .env file into AWS Secrets Manager.
# Secret *names* must already exist (created by: terraform apply in infra/envs/dev).
#
# Usage:
#   ./scripts/push-secrets-to-aws.sh
#   ./scripts/push-secrets-to-aws.sh --env-file /path/.env
#   B4BUILD_PROJECT=acme B4BUILD_ENV=prod ./scripts/push-secrets-to-aws.sh
#   ./scripts/push-secrets-to-aws.sh --dry-run
#
# By default this does NOT overwrite DATABASE_URL — Terraform + RDS set that. Use
#   --include-database-url only if you intentionally need to override (advanced).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

B4BUILD_PROJECT="${B4BUILD_PROJECT:-b4build}"
B4BUILD_ENV="${B4BUILD_ENV:-dev}"
AWS_REGION="${AWS_REGION:-us-east-1}"
DRY_RUN=0
ENV_FILE=""
INCLUDE_DB_URL=0

usage() {
  echo "Usage: $0 [options]"
  echo "  --env-file PATH   Default: first of .env, then backend/.env (repo root)"
  echo "  --dry-run         Print actions only, do not call AWS"
  echo "  --include-database-url  Also push DATABASE_URL to ${B4BUILD_PROJECT}/${B4BUILD_ENV}/database-url (usually wrong for RDS; skip)"
  echo "  Env: B4BUILD_PROJECT (default b4build), B4BUILD_ENV (default dev), AWS_REGION"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --env-file) ENV_FILE="${2:-}"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    --include-database-url) INCLUDE_DB_URL=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
done

if [[ -z "$ENV_FILE" ]]; then
  if [[ -f "$REPO_ROOT/.env" ]]; then
    ENV_FILE="$REPO_ROOT/.env"
  elif [[ -f "$REPO_ROOT/backend/.env" ]]; then
    ENV_FILE="$REPO_ROOT/backend/.env"
  else
    echo "error: no .env found. Copy .env.example and create $REPO_ROOT/.env (or backend/.env)" >&2
    echo "  or pass: --env-file /path/to/.env" >&2
    exit 1
  fi
fi

if [[ ! -f "$ENV_FILE" ]]; then
  echo "error: file not found: $ENV_FILE" >&2
  exit 1
fi

# Load only the keys we map to Secrets Manager. First = in line splits key/value; strip optional quotes.
load_env_file() {
  local f="$1" line key val
  while IFS= read -r line || [[ -n "$line" ]]; do
    line="${line%$'\r'}"
    [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
    [[ ! "$line" =~ ^[A-Za-z_][A-Za-z0-9_]*= ]] && continue
    key="${line%%=*}"
    val="${line#*=}"
    if [[ "$val" =~ ^\".*\"$ ]]; then val="${val#\"}"; val="${val%\"}"; fi
    if [[ "$val" =~ ^\'.*\'$ ]]; then val="${val#\'}"; val="${val%\'}"; fi
    case "$key" in
      OPENAI_API_KEY)   OPENAI_API_KEY="$val" ;;
      TAVILY_API_KEY)  TAVILY_API_KEY="$val" ;;
      CLERK_SECRET_KEY) CLERK_SECRET_KEY="$val" ;;
      SENTRY_DSN)      SENTRY_DSN="$val" ;;
      DATABASE_URL)    DATABASE_URL="$val" ;;
    esac
  done < "$f"
}

if ! command -v aws &>/dev/null; then
  echo "error: aws CLI not found" >&2
  exit 1
fi

load_env_file "$ENV_FILE"

put_secret() {
  local name="$1"
  local value="${2-}"

  if [[ -z "$value" ]]; then
    echo "  skip: $name (empty value in $ENV_FILE)"
    return
  fi

  if [[ "$DRY_RUN" -eq 1 ]]; then
    local masked="${value:0:4}...(${#value} chars)"
    echo "  [dry-run] would put: $name -> $masked"
    return
  fi

  aws secretsmanager put-secret-value \
    --region "$AWS_REGION" \
    --secret-id "$name" \
    --secret-string "$value" \
    >/dev/null
  echo "  ok:   $name"
}

echo "Using: ENV_FILE=$ENV_FILE"
echo "      Secrets prefix: $B4BUILD_PROJECT/$B4BUILD_ENV/  (region $AWS_REGION)"
if [[ "$DRY_RUN" -eq 1 ]]; then
  echo "(dry-run — no changes)"
fi

# Maps env vars from .env to Terraform secret names in secrets_core.tf
put_secret "$B4BUILD_PROJECT/$B4BUILD_ENV/openai-api-key" "${OPENAI_API_KEY-}"
put_secret "$B4BUILD_PROJECT/$B4BUILD_ENV/tavily-api-key" "${TAVILY_API_KEY-}"
put_secret "$B4BUILD_PROJECT/$B4BUILD_ENV/clerk-secret-key" "${CLERK_SECRET_KEY-}"
put_secret "$B4BUILD_PROJECT/$B4BUILD_ENV/sentry-dsn" "${SENTRY_DSN-}"

if [[ "$INCLUDE_DB_URL" -eq 1 ]]; then
  put_secret "$B4BUILD_PROJECT/$B4BUILD_ENV/database-url" "${DATABASE_URL-}"
else
  echo "  note: DATABASE_URL not pushed (Terraform + RDS set this; use --include-database-url to override — usually not for ECS/RDS)"
fi

echo "Done. Redeploy ECS or wait for the next task refresh if the service already used old values."
