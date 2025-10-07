# DynamoDB Tables for RateLock
# Creates tables for rate caching and audit logging

# Rate Cache Table - For storing current exchange rates
resource "aws_dynamodb_table" "rate_cache" {
  name           = "RateCacheTable"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "RateSnapshotID"

  attribute {
    name = "RateSnapshotID"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }

  tags = merge(var.common_tags, {
    Name        = "${var.project_name}-${var.environment}-rate-cache"
    Component   = "database"
    TableType   = "rate-cache"
  })
}

# Conversion Audit Log Table - Immutable audit records
resource "aws_dynamodb_table" "audit_log" {
  name           = "ConversionAuditLogTable"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "AuditLogTransactionID"

  attribute {
    name = "AuditLogTransactionID"
    type = "S"
  }

  point_in_time_recovery {
    enabled = var.enable_point_in_time_recovery
  }

  tags = merge(var.common_tags, {
    Name        = "${var.project_name}-${var.environment}-audit-log"
    Component   = "database"
    TableType   = "audit-log"
  })
}