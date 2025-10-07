# RateLock Development Environment
# This file defines the infrastructure for the development environment

terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

# Configure AWS Provider
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
      CreatedBy   = "ratelock-dev-team"
    }
  }
}

# Local values for common configuration
locals {
  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
    CreatedBy   = "ratelock-dev-team"
  }
}

# Database Module - DynamoDB tables
module "database" {
  source = "../../modules/database"
  
  project_name                   = var.project_name
  environment                   = var.environment
  enable_point_in_time_recovery = var.enable_point_in_time_recovery
  common_tags                   = local.common_tags
}

# Compute Module - ECS, ALB, ECR
module "compute" {
  source = "../../modules/compute"
  
  project_name            = var.project_name
  environment            = var.environment
  aws_region             = var.aws_region
  rate_cache_table_name  = module.database.rate_cache_table_name
  rate_cache_table_arn   = module.database.rate_cache_table_arn
  audit_log_table_name   = module.database.audit_log_table_name
  audit_log_table_arn    = module.database.audit_log_table_arn
  common_tags            = local.common_tags
  
  depends_on = [module.database]
}

# Frontend Module - S3 Static Website
module "frontend" {
  source = "../../modules/frontend"

  project_name    = var.project_name
  environment     = var.environment
  aws_region      = var.aws_region
  common_tags     = local.common_tags
  api_base_url    = module.compute.alb_dns_name
  
  depends_on = [module.compute]
}