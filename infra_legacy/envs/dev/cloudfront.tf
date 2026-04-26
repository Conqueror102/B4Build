# CloudFront Origin Access Identity for S3
resource "aws_cloudfront_origin_access_identity" "pdfs" {
  comment = "OAI for ${var.project_name} PDFs"
}

# S3 bucket policy to allow CloudFront access
resource "aws_s3_bucket_policy" "pdfs_cloudfront" {
  bucket = aws_s3_bucket.pdfs.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid    = "AllowCloudFrontAccess"
      Effect = "Allow"
      Principal = {
        AWS = aws_cloudfront_origin_access_identity.pdfs.iam_arn
      }
      Action   = "s3:GetObject"
      Resource = "${aws_s3_bucket.pdfs.arn}/*"
    }]
  })
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "pdfs" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "${var.project_name} PDF CDN"
  default_root_object = ""
  price_class         = "PriceClass_100" # US, Canada, Europe only (cheapest)

  origin {
    domain_name = aws_s3_bucket.pdfs.bucket_regional_domain_name
    origin_id   = "S3-${aws_s3_bucket.pdfs.id}"

    s3_origin_config {
      origin_access_identity = aws_cloudfront_origin_access_identity.pdfs.cloudfront_access_identity_path
    }
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-${aws_s3_bucket.pdfs.id}"

    forwarded_values {
      query_string = false
      headers      = ["Origin", "Access-Control-Request-Headers", "Access-Control-Request-Method"]

      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
    compress               = true
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-cdn"
  }
}

# CloudWatch Alarms for CloudFront
resource "aws_cloudwatch_metric_alarm" "cloudfront_error_rate" {
  alarm_name          = "${var.project_name}-${var.environment}-cloudfront-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "5xxErrorRate"
  namespace           = "AWS/CloudFront"
  period              = 300
  statistic           = "Average"
  threshold           = 5
  alarm_description   = "CloudFront 5xx error rate is too high"

  dimensions = {
    DistributionId = aws_cloudfront_distribution.pdfs.id
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-cloudfront-error-alarm"
  }
}
