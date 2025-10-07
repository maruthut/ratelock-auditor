# Deployment Summary Output
output "deployment_summary" {
  description = "Summary of all deployed resources"
  value = {
    environment = var.environment
    region      = var.aws_region
    cluster     = module.compute.cluster_name
    load_balancer = module.compute.alb_dns_name
    frontend_url = module.frontend.website_url
    database_tables = {
      rate_cache = module.database.rate_cache_table_name
      audit_log  = module.database.audit_log_table_name
    }
    container_repositories = {
      conversion_engine = module.compute.conversion_engine_repository_url
      ratesync         = module.compute.ratesync_repository_url
    }
  }
}

# Database Outputs
output "rate_cache_table_name" {
  description = "Name of the rate cache DynamoDB table"
  value       = module.database.rate_cache_table_name
}

output "audit_log_table_name" {
  description = "Name of the audit log DynamoDB table"
  value       = module.database.audit_log_table_name
}

# Compute Outputs
output "cluster_name" {
  description = "Name of the ECS cluster"
  value       = module.compute.cluster_name
}

output "alb_dns_name" {
  description = "DNS name of the Application Load Balancer"
  value       = module.compute.alb_dns_name
}

output "conversion_engine_repository_url" {
  description = "URL of the Conversion Engine ECR repository"
  value       = module.compute.conversion_engine_repository_url
}

output "ratesync_repository_url" {
  description = "URL of the RateSync ECR repository"
  value       = module.compute.ratesync_repository_url
}

# Frontend outputs
output "frontend_url" {
  description = "URL of the frontend website"
  value       = module.frontend.website_url
}

output "frontend_bucket_name" {
  description = "Name of the S3 bucket hosting the frontend"
  value       = module.frontend.website_bucket_name
}