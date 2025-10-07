# S3 Static Website Hosting for RateLock Frontend

# S3 bucket for static website hosting
resource "aws_s3_bucket" "website" {
  bucket = "${var.project_name}-frontend-${var.environment}-${random_id.bucket_suffix.hex}"

  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-${var.environment}-frontend-bucket"
    Component = "frontend"
  })
}

# Generate random suffix for bucket name to ensure uniqueness
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# Configure website hosting
resource "aws_s3_bucket_website_configuration" "website" {
  bucket = aws_s3_bucket.website.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "error.html"
  }
}

# Configure public access (for static website)
resource "aws_s3_bucket_public_access_block" "website" {
  bucket = aws_s3_bucket.website.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# Bucket policy for public read access
resource "aws_s3_bucket_policy" "website" {
  bucket = aws_s3_bucket.website.id
  depends_on = [aws_s3_bucket_public_access_block.website]

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.website.arn}/*"
      }
    ]
  })
}

# CORS configuration for API calls
resource "aws_s3_bucket_cors_configuration" "website" {
  bucket = aws_s3_bucket.website.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "POST", "PUT", "DELETE", "HEAD"]
    allowed_origins = ["*"]
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# Upload frontend files
locals {
  # Read the original HTML file and replace the API URL placeholder
  index_html_content = replace(
    file("${path.root}/../../../frontend/index.html"),
    "{{API_BASE_URL}}",
    "http://${var.api_base_url}"
  )
}

resource "aws_s3_object" "index" {
  bucket       = aws_s3_bucket.website.id
  key          = "index.html"
  content      = local.index_html_content
  content_type = "text/html"
  etag         = md5(local.index_html_content)

  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-${var.environment}-index"
    Component = "frontend"
  })
}

# Create a simple error page
resource "aws_s3_object" "error" {
  bucket       = aws_s3_bucket.website.id
  key          = "error.html"
  content_type = "text/html"
  content = <<-EOF
    <!DOCTYPE html>
    <html>
    <head>
        <title>RateLock - Error</title>
        <style>
            body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
            h1 { color: #d32f2f; }
        </style>
    </head>
    <body>
        <h1>Oops! Page Not Found</h1>
        <p>The page you're looking for doesn't exist.</p>
        <a href="/">Return to RateLock</a>
    </body>
    </html>
  EOF

  tags = merge(var.common_tags, {
    Name      = "${var.project_name}-${var.environment}-error"
    Component = "frontend"
  })
}