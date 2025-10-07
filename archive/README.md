# Archive - Legacy Implementation

This folder contains the previous implementation attempts that were replaced with more reliable solutions.

## CDK Implementation (DEPRECATED)
- **Folder**: `cdk-legacy/`
- **Status**: Deprecated due to unreliable deployments and state management issues
- **Issues**: CDK deployments would hang, state inconsistencies between CDK and actual AWS resources
- **Replaced by**: Terraform implementation (see `/terraform/` folder)

## Files Archived:
- `cdk-legacy/` - Original CDK infrastructure code
- `cdk.out-legacy/` - CDK build outputs
- `deploy-aws-cdk.ps1` - PowerShell script for CDK deployment

## Migration Notes:
- Database stack (DynamoDB tables) was successfully deployed with CDK but removed for clean Terraform migration
- Compute stack consistently failed at ECS service creation (22/24 resources would deploy then hang)
- API and Frontend stacks were never successfully deployed due to compute stack dependency

## Lessons Learned:
1. CDK abstractions can hide important AWS resource creation details
2. CDK state management can become inconsistent with actual AWS state
3. Debugging CDK issues is significantly harder than debugging Terraform
4. Terraform provides better visibility and control over infrastructure deployment

**Date Archived**: October 6, 2025
**Reason**: Migrating to Terraform for reliable, repeatable deployments