#!/usr/bin/env bash
# Diagnose 503 / unhealthy ALB + ECS: target health, service, tasks, recent logs.
# Defaults match infra/envs/dev: cluster b4build-dev, service b4build-backend, log /ecs/b4build-dev
#
# Usage:
#   ./scripts/check-ecs-alb-health.sh
#   AWS_REGION=us-west-2 NAME_PREFIX=acme-staging ./scripts/check-ecs-alb-health.sh
#   ALB_NAME=my-alb-xxx   # if not ${NAME_PREFIX}-alb
#
# Requires: aws CLI, curl (for /health).

set -euo pipefail

: "${AWS_REGION:=us-east-1}"
: "${NAME_PREFIX:=b4build-dev}"
: "${ECS_CLUSTER:=$NAME_PREFIX}"
: "${ECS_SERVICE:=b4build-backend}"
: "${LOG_GROUP:=/ecs/${NAME_PREFIX}}"
: "${ALB_NAME:=${NAME_PREFIX}-alb}"
: "${HEALTH_PATH:=/health}"

export AWS_PAGER=""

echo "== Config (override with env) =="
echo "  AWS_REGION=$AWS_REGION  ECS_CLUSTER=$ECS_CLUSTER  ECS_SERVICE=$ECS_SERVICE"
echo "  ALB_NAME=$ALB_NAME  LOG_GROUP=$LOG_GROUP  HEALTH_PATH=$HEALTH_PATH"
echo

if ! command -v aws &>/dev/null; then
  echo "error: aws CLI not found" >&2
  exit 1
fi

echo "== Application Load Balancer: $ALB_NAME =="
if ! ALB_ARN=$(aws elbv2 describe-load-balancers --region "$AWS_REGION" --names "$ALB_NAME" --query 'LoadBalancers[0].LoadBalancerArn' --output text 2>/dev/null) || [[ -z "$ALB_ARN" || "$ALB_ARN" == "None" ]]; then
  echo "  error: no load balancer named $ALB_NAME. Set ALB_NAME=... or NAME_PREFIX=..." >&2
  exit 1
fi
ALB_DNS=$(aws elbv2 describe-load-balancers --region "$AWS_REGION" --names "$ALB_NAME" --query 'LoadBalancers[0].DNSName' --output text)
echo "  DNS: $ALB_DNS"
if command -v curl &>/dev/null; then
  URL="http://${ALB_DNS}${HEALTH_PATH}"
  CODE=$(curl -sS -o /dev/null -w "%{http_code}" --connect-timeout 10 "$URL" || echo "err")
  echo "  GET $URL  ->  HTTP $CODE  (200 if healthy; 503 = often no healthy targets)"
else
  echo "  (install curl to probe $HEALTH_PATH)"
fi
echo

echo "== Target groups =="
TG_ARNS=$(aws elbv2 describe-target-groups --region "$AWS_REGION" --load-balancer-arn "$ALB_ARN" --query 'TargetGroups[].TargetGroupArn' --output text)
if [[ -z "$TG_ARNS" || "$TG_ARNS" == "None" ]]; then
  echo "  error: no target groups on this load balancer" >&2
  exit 1
fi
for TG_ARN in $TG_ARNS; do
  NAME=$(aws elbv2 describe-target-groups --region "$AWS_REGION" --target-group-arns "$TG_ARN" --query 'TargetGroups[0].TargetGroupName' --output text)
  PORT=$(aws elbv2 describe-target-groups --region "$AWS_REGION" --target-group-arns "$TG_ARN" --query 'TargetGroups[0].Port' --output text)
  echo "  Target group: $NAME  (port $PORT)"
  echo "  Target health:"
  aws elbv2 describe-target-health --region "$AWS_REGION" --target-group-arn "$TG_ARN" --output table || true
  echo
done

echo "== ECS service: $ECS_CLUSTER / $ECS_SERVICE =="
aws ecs describe-services --region "$AWS_REGION" --cluster "$ECS_CLUSTER" --services "$ECS_SERVICE" \
  --query 'services[0].{Desired:desiredCount,Running:runningCount,Pending:pendingCount,Status:status}' --output table 2>/dev/null || echo "  (check cluster/service names)"
echo "  Recent service events (first 6):"
aws ecs describe-services --region "$AWS_REGION" --cluster "$ECS_CLUSTER" --services "$ECS_SERVICE" \
  --query 'services[0].events[:6].[createdAt,message]' --output table 2>/dev/null || true
echo

echo "== ECS tasks =="
TASKS=$(aws ecs list-tasks --region "$AWS_REGION" --cluster "$ECS_CLUSTER" --service-name "$ECS_SERVICE" --query 'taskArns' --output text)
if [[ -z "$TASKS" || "$TASKS" == "None" ]]; then
  echo "  no task ARNs — nothing running to serve traffic"
else
  for T in $TASKS; do
    echo "  $T"
    aws ecs describe-tasks --region "$AWS_REGION" --cluster "$ECS_CLUSTER" --tasks "$T" \
      --query 'tasks[0].{lastStatus:lastStatus,desired:desiredStatus,health:healthStatus,stop:stoppedReason}' --output table 2>/dev/null || true
  done
  aws ecs describe-tasks --region "$AWS_REGION" --cluster "$ECS_CLUSTER" --tasks $TASKS \
    --query 'tasks[0].containers[0].{name:name,exit:exitCode,reason:reason}' --output table 2>/dev/null || true
fi
echo

echo "== CloudWatch: $LOG_GROUP (last 5m) =="
if aws logs describe-log-groups --region "$AWS_REGION" --log-group-name-prefix "$LOG_GROUP" --query 'logGroups[0].logGroupName' --output text 2>/dev/null | grep -q .; then
  if aws logs tail "$LOG_GROUP" --region "$AWS_REGION" --since 5m --format short 2>/dev/null | head -100; then
    :
  else
    LATEST=$(aws logs describe-log-streams --region "$AWS_REGION" --log-group-name "$LOG_GROUP" --order-by LastEventTime --descending --max-items 1 --query 'logStreams[0].logStreamName' --output text 2>/dev/null || true)
    if [[ -n "$LATEST" && "$LATEST" != "None" ]]; then
      aws logs get-log-events --region "$AWS_REGION" --log-group-name "$LOG_GROUP" --log-stream-name "$LATEST" --limit 30 --output text 2>/dev/null | head -50 || true
    else
      echo "  (no log streams; tasks may not have started yet)"
    fi
  fi
else
  echo "  log group not found. Set LOG_GROUP= to match Terraform: /ecs/<project>-<env>"
fi

echo
echo "== Done. 503 -> usually 0 healthy targets: fix health check, image, task crash (see logs), SGs. =="
