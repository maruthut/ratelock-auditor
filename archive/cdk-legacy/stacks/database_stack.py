"""
Database Stack for RateLock
Creates DynamoDB tables for rate caching and audit logging
"""

from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
    RemovalPolicy,
    CfnOutput,
    Environment
)
from constructs import Construct


class DatabaseStack(Stack):
    """DynamoDB tables for RateLock currency conversion service"""

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Determine removal policy based on environment
        # Use DESTROY for dev/test, RETAIN for production
        removal_policy = RemovalPolicy.DESTROY
        point_in_time_recovery = False
        
        # In production, use more conservative settings
        env_name = self.node.try_get_context("environment")
        if env_name == "production":
            removal_policy = RemovalPolicy.RETAIN
            point_in_time_recovery = True

        # Rate Cache Table - For storing current exchange rates
        self.rate_cache_table = dynamodb.Table(
            self, "RateCacheTable",
            table_name="RateCacheTable",
            partition_key=dynamodb.Attribute(
                name="RateSnapshotID",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            time_to_live_attribute="ttl",  # Auto-cleanup after 30 days
            removal_policy=removal_policy,
            point_in_time_recovery=point_in_time_recovery,
        )

        # Conversion Audit Log Table - Immutable audit records
        self.audit_log_table = dynamodb.Table(
            self, "ConversionAuditLogTable", 
            table_name="ConversionAuditLogTable",
            partition_key=dynamodb.Attribute(
                name="AuditLogTransactionID",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=removal_policy,
            point_in_time_recovery=point_in_time_recovery,
            
            # Add GSI for querying by timestamp (future enhancement)
            # global_secondary_indexes=[
            #     dynamodb.GlobalSecondaryIndex(
            #         index_name="TimestampIndex",
            #         partition_key=dynamodb.Attribute(
            #             name="ConversionTimestamp",
            #             type=dynamodb.AttributeType.STRING
            #         )
            #     )
            # ]
        )

        # Outputs for other stacks
        CfnOutput(
            self, "RateCacheTableName",
            value=self.rate_cache_table.table_name,
            description="Name of the Rate Cache DynamoDB table",
            export_name="RateLock-RateCacheTableName"
        )

        CfnOutput(
            self, "RateCacheTableArn",
            value=self.rate_cache_table.table_arn,
            description="ARN of the Rate Cache DynamoDB table",
            export_name="RateLock-RateCacheTableArn"
        )

        CfnOutput(
            self, "AuditLogTableName", 
            value=self.audit_log_table.table_name,
            description="Name of the Audit Log DynamoDB table",
            export_name="RateLock-AuditLogTableName"
        )

        CfnOutput(
            self, "AuditLogTableArn",
            value=self.audit_log_table.table_arn,
            description="ARN of the Audit Log DynamoDB table", 
            export_name="RateLock-AuditLogTableArn"
        )