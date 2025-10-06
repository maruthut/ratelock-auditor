# 🚀 RateLock - Dual Environment Setup Guide

**Auditable Currency Conversion API with Local Development + AWS Deployment**

## 🎯 Quick Start

### 🏠 **Local Development (Start here!)**
```powershell
# Start local environment
.\start-local.ps1

# Test locally
python test_local.py
```
**Ready in 2 minutes!** 🌐 http://localhost:3000

### ☁️ **AWS Deployment (Production ready!)**
```powershell
# Deploy to AWS
.\deploy-aws.ps1

# Test AWS deployment
python scripts\test_aws.py
```

## 🏗️ **Architecture Overview**

### **Local Development Stack:**
```
Windows Desktop
├── 🐳 Docker Compose
│   ├── ConversionEngine (FastAPI) → localhost:8080
│   ├── RateSync (FastAPI) → Background worker
│   ├── DynamoDB Local → localhost:8000
│   └── Frontend (Nginx) → localhost:3000
└── 🧪 Testing Scripts (Python)
```

### **AWS Production Stack:**
```
AWS Cloud
├── 🌐 S3 Static Website
├── 🚪 API Gateway
├── ⚖️ Application Load Balancer
├── 🐳 ECS Fargate Services
│   ├── ConversionEngine (FastAPI)
│   └── RateSync (EventBridge Scheduled)
├── 🗄️ DynamoDB Tables
└── 📊 CloudWatch Monitoring
```

## 📁 **Project Structure**

```
ratelock-auditor/
├── 🐳 Local Development
│   ├── docker-compose.yml         # Local orchestration
│   ├── setup_local_db.py         # Local DynamoDB setup
│   ├── test_local.py             # Local testing
│   ├── start-local.ps1           # Local startup script
│   ├── start_local.bat           # Legacy batch file
│   ├── start_local.ps1           # Additional PS1 file
│   ├── nginx.conf               # Local Nginx configuration
│   ├── dev-requirements.txt     # Development dependencies
│   └── LOCAL_TESTING.md         # Local development guide
│
├── ☁️ AWS Infrastructure
│   ├── cdk/                     # CDK Infrastructure code
│   │   ├── app.py              # CDK entry point
│   │   ├── cdk.json            # CDK configuration
│   │   ├── requirements.txt    # CDK dependencies
│   │   └── stacks/             # Individual CDK stacks
│   │       ├── __init__.py         # Python package init
│   │       ├── database_stack.py   # DynamoDB tables
│   │       ├── compute_stack.py    # ECS Fargate services
│   │       ├── api_stack.py        # API Gateway
│   │       └── frontend_stack.py   # S3 static website
│   ├── scripts/
│   │   ├── deploy_aws.py       # AWS deployment automation
│   │   └── test_aws.py         # AWS testing
│   └── deploy-aws.ps1          # AWS deployment script
│
├── 📦 Application Services (SHARED!)
│   ├── service-conversion/      # ConversionEngine FastAPI service
│   │   ├── conversionengine.py # Main FastAPI application
│   │   ├── requirements.txt    # Python dependencies
│   │   └── Dockerfile         # Container configuration
│   ├── service-ratesync/       # RateSync FastAPI service
│   │   ├── ratesync.py        # Rate fetching service
│   │   ├── requirements.txt   # Python dependencies
│   │   └── Dockerfile        # Container configuration
│   └── frontend/              # Single-page application
│       └── index.html        # Environment-aware frontend
│
├── 📂 Generated Folders
│   └── logs/                  # Application logs directory
│
└── 📚 Documentation
    ├── .gitignore             # Git ignore rules
    ├── README.md              # Original project documentation
    ├── README-DUAL-ENVIRONMENT.md # This guide
    ├── MasterPrompt           # Project specification
    └── LOCAL_TESTING.md       # Local testing guide
```

## 🛠️ **Prerequisites**

### **For Local Development:**
- ✅ **Docker Desktop** (Windows)
- ✅ **Python 3.9+** with pip
- ✅ **PowerShell** (default in Windows)
- ✅ **Git** (for version control)

### **For AWS Deployment:**
- ✅ **AWS CLI** configured with credentials
- ✅ **Node.js 18+** (for AWS CDK)
- ✅ **AWS CDK** (`npm install -g aws-cdk`)
- ✅ **Active AWS Account** with appropriate permissions

## 🏠 **Local Development Workflow**

### **1. Initial Setup**
```powershell
# Clone repository (if not already done)
git clone https://github.com/maruthut/ratelock-auditor.git
cd ratelock-auditor

# Start local development environment
.\start-local.ps1
```

### **2. Development Cycle**
```powershell
# Make code changes in service-*/
# Auto-reload is enabled in Docker containers

# Test changes
python test_local.py

# View logs
docker-compose logs -f
```

### **3. Local Access Points**
- **Frontend**: http://localhost:3000
- **ConversionEngine API**: http://localhost:8080
- **RateSync Health**: http://localhost:8081/health
- **DynamoDB Admin**: http://localhost:8001

## ☁️ **AWS Deployment Workflow**

### **1. Prerequisites Check**
```powershell
# Verify AWS configuration
aws sts get-caller-identity

# Verify CDK installation
cdk --version

# Bootstrap CDK (one-time setup)
cdk bootstrap
```

### **2. Deploy to AWS**
```powershell
# Deploy complete infrastructure
.\deploy-aws.ps1

# Monitor deployment
# Follow the logs and CloudFormation console
```

### **3. Test AWS Deployment**
```powershell
# Run comprehensive AWS tests
python scripts\test_aws.py
```

## 🔄 **Environment Synchronization**

The dual environment is designed to keep local development and AWS production in sync:

### **Shared Components:**
- ✅ **Same Docker images** used locally and in ECS
- ✅ **Same Python code** (service-conversion/, service-ratesync/)
- ✅ **Same database schema** (DynamoDB tables)
- ✅ **Same API contracts** (OpenAPI/FastAPI)

### **Environment-Specific Configurations:**
- 🏠 **Local**: DynamoDB Local, Docker Compose networking
- ☁️ **AWS**: DynamoDB service, ECS Fargate, API Gateway

### **Automatic Environment Detection:**
```python
# In application code (conversionengine.py, ratesync.py)
if os.getenv('AWS_EXECUTION_ENV'):
    # Running in AWS ECS
    dynamodb = boto3.resource('dynamodb')
else:
    # Running locally
    dynamodb = boto3.resource('dynamodb', endpoint_url='http://dynamodb-local:8000')
```

## 🧪 **Testing Strategy**

### **Local Testing**
```powershell
# Quick health check
python test_local.py --quick

# Full regression test
python test_local.py --full

# Performance testing
python test_local.py --load
```

### **AWS Testing**
```powershell
# Infrastructure validation
python scripts\test_aws.py --infra

# End-to-end testing
python scripts\test_aws.py --e2e

# Load testing
python scripts\test_aws.py --load
```

## 🚀 **Deployment Commands Reference**

### **Local Environment**
```powershell
# Start services
.\start-local.ps1

# Stop services
docker-compose down

# Rebuild and restart
docker-compose down && docker-compose build && docker-compose up -d

# View logs
docker-compose logs -f [service-name]

# Clean up
docker-compose down -v  # Removes volumes too
```

### **AWS Environment**
```powershell
# Deploy all stacks
.\deploy-aws.ps1

# Deploy specific stack
cdk deploy RateLockDatabaseStack

# Destroy environment
cdk destroy --all

# View CloudFormation outputs
aws cloudformation describe-stacks --stack-name RateLockApiStack --query 'Stacks[0].Outputs'
```

## 🔍 **Troubleshooting**

### **Local Development Issues**

**Problem**: Docker containers not starting
```powershell
# Solution: Check Docker Desktop status
docker info
docker-compose ps
```

**Problem**: DynamoDB Local not accessible
```powershell
# Solution: Verify container and port mapping
docker-compose logs dynamodb-local
curl http://localhost:8000
```

**Problem**: Services not communicating
```powershell
# Solution: Check Docker network
docker network ls
docker-compose exec conversion-engine ping dynamodb-local
```

### **AWS Deployment Issues**

**Problem**: CDK bootstrap fails
```powershell
# Solution: Check AWS credentials and permissions
aws sts get-caller-identity
cdk bootstrap --show-template
```

**Problem**: ECS tasks failing to start
```powershell
# Solution: Check CloudWatch logs
aws logs describe-log-groups --log-group-name-prefix="/ecs/ratelock"
aws ecs describe-services --cluster RateLockCluster --services ConversionEngineService
```

**Problem**: API Gateway timeouts
```powershell
# Solution: Check ALB and ECS health
aws elbv2 describe-target-health --target-group-arn [target-group-arn]
```

## 📊 **Monitoring and Observability**

### **Local Monitoring**
- **Docker Compose**: `docker-compose ps` and `docker-compose logs`
- **Health Endpoints**: All services expose `/health` endpoints
- **DynamoDB Local**: Web UI at http://localhost:8001

### **AWS Monitoring**
- **CloudWatch**: Automatic logging and metrics for all services
- **ECS Console**: Service status and task health
- **API Gateway**: Request/response logs and latency metrics
- **DynamoDB**: Read/write capacity and throttling metrics

## 🎯 **Development Best Practices**

### **Code Changes**
1. **Develop locally first** using `.\start-local.ps1`
2. **Test thoroughly** with `python test_local.py`
3. **Commit changes** to version control
4. **Deploy to AWS** with `.\deploy-aws.ps1`
5. **Validate AWS deployment** with `python scripts\test_aws.py`

### **Infrastructure Changes**
1. **Modify CDK stacks** in `cdk/stacks/`
2. **Test locally** if possible (database schema changes)
3. **Deploy to AWS** with CDK
4. **Validate** with AWS console and testing scripts

### **Database Schema Changes**
1. **Update** `setup_local_db.py` for local development
2. **Update** CDK `database_stack.py` for AWS
3. **Test migration** locally first
4. **Deploy** to AWS with proper backup strategy

## 🎉 **Success Metrics**

After successful dual environment setup, you should have:

✅ **Local Development**:
- Frontend accessible at http://localhost:3000
- All API endpoints working via http://localhost:8080
- DynamoDB Local with proper table structure
- Docker containers healthy and communicating

✅ **AWS Production**:
- S3 static website with custom domain (optional)
- API Gateway with proper CORS and rate limiting
- ECS Fargate services running and healthy
- DynamoDB tables with proper TTL settings
- CloudWatch logging and monitoring active

✅ **Dual Environment Sync**:
- Same codebase running in both environments
- Same API contracts and behavior
- Same database schema and operations
- Seamless development workflow between local and AWS

---

## 🆘 **Support and Resources**

- **Project Issues**: Check `LOCAL_TESTING.md` for common problems
- **AWS CDK Docs**: [AWS CDK Developer Guide](https://docs.aws.amazon.com/cdk/)
- **FastAPI Docs**: [FastAPI Documentation](https://fastapi.tiangolo.com/)
- **Docker Compose**: [Docker Compose Reference](https://docs.docker.com/compose/)

**Happy coding with RateLock dual environment! 🚀**