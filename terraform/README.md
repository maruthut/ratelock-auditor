# RateLock Infrastructure - Terraform

This directory contains the Terraform Infrastructure as Code (IaC) for deploying the complete RateLock microservices currency conversion application to AWS.

## 🏗️ Deployed Architecture Overview

The infrastructure uses a modular microservices architecture with load balancing:

- **Frontend**: S3 static website hosting with public access
- **Load Balancer**: Application Load Balancer for traffic distribution
- **Compute**: ECS Fargate cluster with auto-scaling microservices
- **Database**: DynamoDB tables for rate caching and audit logging
- **Security**: IAM roles, security groups, and least-privilege access
- **Monitoring**: CloudWatch logs and application metrics

## 📁 Directory Structure

```
terraform/
├── modules/                 # Deployed Terraform modules
│   ├── database/           # ✅ DynamoDB tables module (deployed)
│   ├── compute/            # ✅ ECS, ALB, ECR module (deployed)
│   └── frontend/           # ✅ S3 static website module (deployed)
├── environments/           # Environment-specific configurations  
│   └── dev/               # ✅ Development environment (deployed)
│       ├── main.tf        # Main infrastructure configuration
│       ├── outputs.tf     # Infrastructure outputs
│       ├── terraform.tf   # Provider and backend configuration
│       └── variables.tf   # Environment variables
└── scripts/               # Deployment automation scripts (future)
    ├── deploy.ps1         # Main deployment script
    ├── status.ps1         # Infrastructure status checker
    └── destroy.ps1        # Safe destruction script
```

## 🌐 Currently Deployed Infrastructure

### Production Environment: `dev` (us-east-2)

**Frontend Layer:**
- **S3 Bucket**: `ratelock-frontend-{env}-{random-suffix}`
- **Website URL**: `http://{bucket-name}.s3-website.{region}.amazonaws.com`
- **Features**: CORS enabled, public access, error handling

**Load Balancing Layer:**
- **ALB**: `{alb-name}.{region}.elb.amazonaws.com`
- **Target Groups**: Health checks for ConversionEngine service
- **Security Groups**: Controlled access (HTTP/80, container port/8080)

**Compute Layer:**
- **ECS Cluster**: `ratelock-{env}-cluster`
- **Services**: RateSync (worker), ConversionEngine (API)
- **ECR Repos**: 
  - `{account-id}.dkr.ecr.{region}.amazonaws.com/ratelock/conversion-engine`
  - `{account-id}.dkr.ecr.{region}.amazonaws.com/ratelock/ratesync`

**Database Layer:**
- **Rate Cache**: `RateCacheTable` (TTL enabled, 31 currencies)
- **Audit Log**: `ConversionAuditLogTable` (permanent retention)

## 🚀 Deployment Instructions

### Prerequisites

1. **Terraform** >= 1.13 installed
2. **AWS CLI** configured with appropriate credentials
3. **PowerShell** for command execution
4. **Docker** for container image building (if modifying services)

### Current Deployment Commands

```powershell
# Navigate to development environment
cd terraform/environments/dev

# Initialize Terraform (first time only)
terraform init

# Plan infrastructure changes
terraform plan

# Apply infrastructure (already deployed)
terraform apply

# Check current deployment status
terraform output deployment_summary

# View all outputs
terraform output
```

### Infrastructure Outputs

```powershell
# View deployed infrastructure details
PS> terraform output deployment_summary

{
  "cluster" = "ratelock-{env}-cluster"
  "container_repositories" = {
    "conversion_engine" = "{account-id}.dkr.ecr.{region}.amazonaws.com/ratelock/conversion-engine"
    "ratesync" = "{account-id}.dkr.ecr.{region}.amazonaws.com/ratelock/ratesync"
  }
  "database_tables" = {
    "audit_log" = "ConversionAuditLogTable"
    "rate_cache" = "RateCacheTable"
  }
  "environment" = "dev"
  "frontend_url" = "http://{bucket-name}.s3-website.{region}.amazonaws.com"
  "load_balancer" = "{alb-name}.{region}.elb.amazonaws.com"
  "region" = "us-east-2"
}
```
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