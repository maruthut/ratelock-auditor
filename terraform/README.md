# RateLock Infrastructure - Terraform

This directory contains the Terraform Infrastructure as Code (IaC) for deploying the RateLock currency conversion application to AWS.

## 🏗️ Architecture Overview

The infrastructure is organized into modular components:

- **Database**: DynamoDB tables for rate caching and audit logging
- **Compute**: ECS Fargate services, Application Load Balancer, ECR repositories
- **API**: API Gateway integration (future enhancement)
- **Frontend**: S3 + CloudFront for React app hosting (future enhancement)

## 📁 Directory Structure

```
terraform/
├── modules/                 # Reusable Terraform modules
│   ├── database/           # DynamoDB tables module
│   ├── compute/            # ECS, ALB, ECR module
│   ├── api/                # API Gateway module (future)
│   └── frontend/           # S3 + CloudFront module (future)
├── environments/           # Environment-specific configurations
│   ├── dev/               # Development environment
│   ├── staging/           # Staging environment (future)
│   └── prod/              # Production environment (future)
└── scripts/               # Deployment automation scripts
    ├── deploy.ps1         # Main deployment script
    ├── status.ps1         # Infrastructure status checker
    └── destroy.ps1        # Safe destruction script
```

## 🚀 Quick Start

### Prerequisites

1. **Terraform** >= 1.0 installed
2. **AWS CLI** configured with appropriate credentials
3. **PowerShell** (for deployment scripts)

### Deploy Development Environment

```powershell
# Navigate to terraform directory
cd C:\Maruthu\Projects\ratelock-auditor\terraform

# Deploy the entire development stack
.\scripts\deploy.ps1 -Environment dev

# Or deploy with auto-approval (no prompts)
.\scripts\deploy.ps1 -Environment dev -AutoApprove
```

### Check Status

```powershell
# Check deployment status
.\scripts\status.ps1 -Environment dev
```

### Destroy Infrastructure

```powershell
# Safely destroy development environment
.\scripts\destroy.ps1 -Environment dev
```

## 🎯 Component-by-Component Deployment

You can deploy individual components if needed:

```powershell
# Deploy only database layer
.\scripts\deploy.ps1 -Environment dev -Component database

# Deploy only compute layer
.\scripts\deploy.ps1 -Environment dev -Component compute
```

## 📊 What Gets Deployed

### Database Layer
- **RateCacheTable**: DynamoDB table for storing current exchange rates
- **AuditLogTable**: DynamoDB table for immutable audit records

### Compute Layer
- **ECS Cluster**: Fargate cluster for running containerized services
- **Application Load Balancer**: HTTP/HTTPS traffic distribution
- **ECR Repositories**: Container image storage
- **Security Groups**: Network access controls
- **IAM Roles**: Service permissions
- **CloudWatch Log Groups**: Application logging

## 🔧 Configuration

### Environment Variables

The deployment is configured through Terraform variables in `environments/{env}/variables.tf`:

- `project_name`: Project identifier (default: "ratelock")
- `environment`: Environment name (dev, staging, prod)
- `aws_region`: AWS region for deployment (default: "us-east-1")
- `enable_point_in_time_recovery`: Enable DynamoDB PITR (default: false for dev)

### Cost Optimization

The development environment is configured for cost efficiency:
- Pay-per-request DynamoDB billing
- Minimal ECS task resources (256 CPU, 512 MB memory)
- No Container Insights (saves CloudWatch costs)
- Short log retention (14 days)

## 🛡️ Security Features

- **IAM Least Privilege**: Services only get required permissions
- **VPC Security Groups**: Network-level access controls
- **ECR Image Scanning**: Container vulnerability scanning
- **HTTPS Ready**: ALB configured for SSL termination

## 🔍 Troubleshooting

### Common Issues

1. **AWS Credentials**: Ensure `aws configure` is properly set up
2. **Terraform State**: If deployment fails, check `terraform.tfstate` file
3. **Resource Limits**: Check AWS service quotas in your region

### Useful Commands

```powershell
# Check AWS credentials
aws sts get-caller-identity

# Validate Terraform configuration
cd environments/dev
terraform validate

# See what would be deployed
terraform plan

# Check current state
terraform show
```

## 🆚 Comparison to CDK

| Aspect | Terraform | CDK |
|--------|-----------|-----|
| **State Management** | Explicit, reliable | Abstract, can be inconsistent |
| **Debugging** | Clear error messages | Complex abstraction layers |
| **Community** | Massive ecosystem | AWS-specific |
| **Learning Curve** | Moderate | Steep |
| **Deployment Speed** | Predictable | Can hang unexpectedly |
| **Multi-Cloud** | Yes | AWS only |

## 📝 Migration Notes

This Terraform setup replaces the previous CDK implementation which experienced:
- Hanging deployments at ECS service creation
- State inconsistencies between CDK and AWS
- Difficult debugging of infrastructure issues

The Terraform approach provides:
- Reliable, repeatable deployments
- Clear state management
- Better error messages and debugging
- Industry-standard tooling

## 🤝 Contributing

When adding new infrastructure:

1. Create modules in `modules/` directory
2. Add environment configuration in `environments/`
3. Update deployment scripts if needed
4. Test in development environment first
5. Document any new variables or outputs

## 📞 Support

For deployment issues:
1. Check the troubleshooting section above
2. Run `.\scripts\status.ps1 -Environment dev` to diagnose
3. Review Terraform logs for specific error messages
4. Check AWS Console for resource status