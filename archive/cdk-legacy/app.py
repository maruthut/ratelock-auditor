#!/usr/bin/env python3
"""
RateLock CDK Application
AWS Infrastructure as Code for auditable currency conversion service
"""

import aws_cdk as cdk
from stacks.database_stack import DatabaseStack
from stacks.compute_stack import ComputeStack
from stacks.api_stack import ApiStack
from stacks.frontend_stack import FrontendStack

app = cdk.App()

# Get environment configuration
environment = app.node.try_get_context("environment") or "dev"
region = app.node.try_get_context("region") or "us-east-1"

# CDK Environment - explicitly set account for VPC lookups
import boto3
import os

# Get account ID from AWS credentials
try:
    sts_client = boto3.client('sts')
    account_id = sts_client.get_caller_identity()['Account']
except Exception:
    # Fallback to environment variable if available
    account_id = os.environ.get('CDK_DEFAULT_ACCOUNT')

env = cdk.Environment(
    account=account_id,
    region=region
)

# Stack naming convention
stack_prefix = f"RateLock-{environment.title()}"

# Database Stack - DynamoDB tables
database_stack = DatabaseStack(
    app, f"{stack_prefix}-Database",
    env=env,
    description=f"RateLock DynamoDB tables for {environment} environment"
)

# Compute Stack - ECS Fargate services  
compute_stack = ComputeStack(
    app, f"{stack_prefix}-Compute",
    database_stack=database_stack,
    env=env,
    description=f"RateLock ECS Fargate services for {environment} environment"
)

# API Stack - API Gateway
api_stack = ApiStack(
    app, f"{stack_prefix}-Api",
    compute_stack=compute_stack,
    env=env,
    description=f"RateLock API Gateway for {environment} environment"
)

# Frontend Stack - S3 Static Website
frontend_stack = FrontendStack(
    app, f"{stack_prefix}-Frontend",
    api_stack=api_stack,
    env=env,
    description=f"RateLock S3 frontend for {environment} environment"
)

# Add tags to all stacks
for stack in [database_stack, compute_stack, api_stack, frontend_stack]:
    cdk.Tags.of(stack).add("Project", "RateLock")
    cdk.Tags.of(stack).add("Environment", environment)
    cdk.Tags.of(stack).add("ManagedBy", "CDK")

app.synth()