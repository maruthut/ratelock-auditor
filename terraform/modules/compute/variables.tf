variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "ratelock"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "rate_cache_table_name" {
  description = "Name of the rate cache DynamoDB table"
  type        = string
}

variable "rate_cache_table_arn" {
  description = "ARN of the rate cache DynamoDB table"
  type        = string
}

variable "audit_log_table_name" {
  description = "Name of the audit log DynamoDB table"
  type        = string
}

variable "audit_log_table_arn" {
  description = "ARN of the audit log DynamoDB table"
  type        = string
}

variable "common_tags" {
  description = "Common tags to apply to all resources"
  type        = map(string)
  default     = {}
}