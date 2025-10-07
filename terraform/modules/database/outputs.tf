output "rate_cache_table_name" {
  description = "Name of the rate cache DynamoDB table"
  value       = aws_dynamodb_table.rate_cache.name
}

output "rate_cache_table_arn" {
  description = "ARN of the rate cache DynamoDB table"
  value       = aws_dynamodb_table.rate_cache.arn
}

output "audit_log_table_name" {
  description = "Name of the audit log DynamoDB table"
  value       = aws_dynamodb_table.audit_log.name
}

output "audit_log_table_arn" {
  description = "ARN of the audit log DynamoDB table"
  value       = aws_dynamodb_table.audit_log.arn
}