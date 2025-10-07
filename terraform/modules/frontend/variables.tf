variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "ratelock"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-2"
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default = {
    Project     = "ratelock"
    Environment = "dev"
    ManagedBy   = "terraform"
    CreatedBy   = "ratelock-dev-team"
  }
}

variable "api_base_url" {
  description = "Base URL for the API (ALB DNS name)"
  type        = string
}