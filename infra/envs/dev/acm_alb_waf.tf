# ACM in the ALB region. DNS validation: add CNAME records at your registrar (no Route 53).
# When ACM shows ISSUED, set enable_https_listener = true and re-apply to attach HTTPS.
resource "aws_acm_certificate" "api" {
  count = var.api_fqdn != "" ? 1 : 0

  domain_name       = var.api_fqdn
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

resource "aws_lb" "main" {
  name     = "${local.name_prefix}-alb" # e.g. b4build-dev-alb (32 char max)
  internal = false

  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = module.vpc.public_subnets
  idle_timeout       = 120
}

resource "aws_lb_target_group" "backend" {
  name_prefix = "b4-"
  port     = var.container_port
  protocol = "HTTP"
  vpc_id   = module.vpc.vpc_id

  target_type = "ip"
  deregistration_delay = 30

  health_check {
    path                = var.health_check_path
    healthy_threshold   = 2
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200"
    port                = "traffic-port"
    protocol            = "HTTP"
  }

  lifecycle {
    create_before_destroy = true
  }
}

# WAF: OWASP + SQLi + simple rate (count large bodies so SSE/JSON still works for chat)
resource "aws_wafv2_web_acl" "alb" {
  name  = "${local.name_prefix}-waf"
  scope = "REGIONAL"

  default_action {
    allow {}
  }


  rule {
    name     = "allow-cors-preflight-options"
    priority = 0
    action {
      allow {}
    }
    statement {
      byte_match_statement {
        positional_constraint = "EXACTLY"
        search_string         = "OPTIONS"
        field_to_match {
          method {}
        }
        text_transformation {
          priority = 0
          type     = "NONE"
        }
      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "cors-options"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "AWS-AWSManagedRulesCommonRuleSet"
    priority = 1
    override_action {
      none {}
    }
    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesCommonRuleSet"
        vendor_name = "AWS"
        rule_action_override {
          name = "SizeRestrictions_BODY"
          action_to_use {
            count {}
          }
        }
      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "crs"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "AWS-AWSManagedRulesKnownBadInputsRuleSet"
    priority = 2
    override_action {
      none {}
    }
    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesKnownBadInputsRuleSet"
        vendor_name = "AWS"
      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "badin"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "AWS-AWSManagedRulesSQLiRuleSet"
    priority = 3
    override_action {
      none {}
    }
    statement {
      managed_rule_group_statement {
        name        = "AWSManagedRulesSQLiRuleSet"
        vendor_name = "AWS"
      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "sqli"
      sampled_requests_enabled   = true
    }
  }

  rule {
    name     = "rate-ips"
    priority = 4
    action {
      block {}
    }
    statement {
      rate_based_statement {
        limit              = 2000
        aggregate_key_type = "IP"
      }
    }
    visibility_config {
      cloudwatch_metrics_enabled = true
      metric_name                = "rate"
      sampled_requests_enabled   = true
    }
  }
  visibility_config {
    cloudwatch_metrics_enabled = true
    metric_name                = "waf-acl"
    sampled_requests_enabled   = true
  }
}

resource "aws_wafv2_web_acl_association" "alb" {
  resource_arn = aws_lb.main.arn
  web_acl_arn  = aws_wafv2_web_acl.alb.arn
}

# HTTP: always forward (works before ACM validation). For HTTPS, add a 443 listener below.
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type = "forward"
    forward {
      target_group { arn = aws_lb_target_group.backend.arn }
    }
  }
}

# Re-apply only after `aws acm` shows ISSUED for the requested domain. Certificate requested above (no Route 53).
resource "aws_lb_listener" "https" {
  count = (var.api_fqdn != "" && var.enable_https_listener) ? 1 : 0

  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-TLS-1-2-2017-01"
  certificate_arn   = aws_acm_certificate.api[0].arn

  default_action {
    type = "forward"
    forward {
      target_group { arn = aws_lb_target_group.backend.arn }
    }
  }
}