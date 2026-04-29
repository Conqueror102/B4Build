# CloudFront in front of the public ALB so the browser sees HTTPS without a custom domain.
#
# Why: an HTTPS Amplify page (https://main.xxx.amplifyapp.com) is blocked by the browser
# from calling http://...elb.amazonaws.com (mixed content). Putting CloudFront in front
# gives a free https://dxxxx.cloudfront.net URL with the AWS-managed *.cloudfront.net cert.
# CloudFront talks HTTP to the ALB on the origin side, so no ACM cert / domain is required.
#
# SSE note: caching is fully disabled (CachingDisabled managed policy) so chat streams pass
# through unmodified. Very long-lived streams may still hit CloudFront idle-timeout limits.
#
# Managed policy IDs (AWS-published, stable):
#   CachingDisabled                  4135ea2d-6df8-44a3-9df3-4b5a84be39ad
#   AllViewerExceptHostHeader        b689b0a8-53d0-40ab-baf2-68738e2966ac

resource "aws_cloudfront_distribution" "api" {
  count = var.create_cloudfront ? 1 : 0

  enabled         = true
  is_ipv6_enabled = true
  comment         = "${local.name_prefix} API in front of ALB (HTTPS for browsers, HTTP to origin)"
  price_class     = "PriceClass_100"
  http_version    = "http2"

  origin {
    domain_name = aws_lb.main.dns_name
    origin_id   = "alb-origin"

    custom_origin_config {
      http_port                = 80
      https_port               = 443
      origin_protocol_policy   = "http-only"
      origin_ssl_protocols     = ["TLSv1.2"]
      origin_read_timeout      = 60
      origin_keepalive_timeout = 60
    }
  }

  default_cache_behavior {
    target_origin_id       = "alb-origin"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods         = ["GET", "HEAD"]
    compress               = false

    cache_policy_id          = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad"
    origin_request_policy_id = "b689b0a8-53d0-40ab-baf2-68738e2966ac"
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  depends_on = [aws_lb.main]
}
