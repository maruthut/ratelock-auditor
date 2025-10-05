# 🧪 Local Testing Guide for RateLock

This guide will help you run and test the complete RateLock system locally using Docker.

## 📋 Prerequisites

### Required Software:
- ✅ **Docker Desktop** (already installed)
- ✅ **Python 3.8+** (for testing tools)
- ✅ **Git** (for version control)

### Optional but Recommended:
- **Postman** or **Insomnia** (for API testing)
- **Visual Studio Code** (for code editing)

## 🚀 Quick Start

### Option 1: Automated Setup (Recommended)
```powershell
# Run the automated setup script
.\start_local.ps1
```

### Option 2: Manual Setup
```powershell
# 1. Install Python dependencies for testing tools
pip install -r dev-requirements.txt

# 2. Start all services with Docker Compose
docker-compose up -d --build

# 3. Wait for services to be ready (about 20 seconds)
Start-Sleep -Seconds 20

# 4. Setup DynamoDB tables
python setup_local_db.py

# 5. Run tests
python test_local.py
```

## 🏗️ What Gets Started

The local environment includes:

### 📊 **Services:**
- **🔄 RateSync Service** - Fetches rates from Frankfurter API
- **💱 ConversionEngine API** - Handles currency conversions
- **🌐 Frontend** - Web interface at http://localhost:3000
- **🗄️ DynamoDB Local** - Local database at http://localhost:8000
- **📋 DynamoDB Admin** - Database viewer at http://localhost:8001

### 🔗 **Endpoints:**
| Service | URL | Purpose |
|---------|-----|---------|
| Frontend | http://localhost:3000 | Web interface |
| API Health | http://localhost:8080/health | Service status |
| Currency Convert | http://localhost:8080/v1/convert | Main API |
| Audit Records | http://localhost:8080/v1/audit/{id} | Compliance |
| DynamoDB Admin | http://localhost:8001 | Database viewer |

## 🧪 Testing the System

### 1. **Automated Tests**
```powershell
python test_local.py
```
This runs comprehensive tests including:
- ✅ Service health checks
- ✅ Currency conversion functionality
- ✅ Audit trail verification
- ✅ Error handling scenarios

### 2. **Manual API Testing**

#### Convert Currency:
```bash
curl "http://localhost:8080/v1/convert?from=USD&to=EUR&amount=100"
```

#### Check Service Health:
```bash
curl "http://localhost:8080/health"
```

#### Get Audit Record:
```bash
curl "http://localhost:8080/v1/audit/{transaction-id}"
```

### 3. **Frontend Testing**
1. Open http://localhost:3000 in your browser
2. Enter amount and select currencies
3. Click "Convert Currency"
4. Verify audit information is displayed

## 📊 Monitoring and Debugging

### View Logs:
```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f conversion-engine
docker-compose logs -f ratesync
```

### Check Service Status:
```powershell
docker-compose ps
```

### Access DynamoDB Admin:
- Open http://localhost:8001
- View tables: `RateCacheTable` and `ConversionAuditLogTable`
- Browse data, create queries, etc.

## 🛠️ Development Workflow

### Making Code Changes:
1. **Edit source code** in `service-conversion/` or `service-ratesync/`
2. **Rebuild affected service**:
   ```powershell
   docker-compose up -d --build conversion-engine
   ```
3. **Test changes**:
   ```powershell
   python test_local.py
   ```

### Frontend Changes:
1. **Edit** `frontend/index.html`
2. **Refresh browser** (no rebuild needed)

### Database Reset:
```powershell
# Stop services and remove data
docker-compose down -v

# Restart and setup
docker-compose up -d --build
python setup_local_db.py
```

## 📋 Common Test Scenarios

### 1. **Basic Conversion Test**
```powershell
# Test USD to EUR conversion
Invoke-RestMethod -Uri "http://localhost:8080/v1/convert?from=USD&to=EUR&amount=100"
```

### 2. **Triangulation Test**
```powershell
# Test non-EUR currencies (uses EUR as pivot)
Invoke-RestMethod -Uri "http://localhost:8080/v1/convert?from=USD&to=GBP&amount=50"
```

### 3. **Error Handling Test**
```powershell
# Test invalid currency
Invoke-RestMethod -Uri "http://localhost:8080/v1/convert?from=INVALID&to=EUR&amount=100"
```

### 4. **Audit Trail Test**
```powershell
# 1. Make conversion and note the audit_log_transaction_id
$result = Invoke-RestMethod -Uri "http://localhost:8080/v1/convert?from=USD&to=EUR&amount=100"

# 2. Retrieve audit record
$auditId = $result.audit_log_transaction_id
Invoke-RestMethod -Uri "http://localhost:8080/v1/audit/$auditId"
```

## ⚠️ Troubleshooting

### Services Won't Start:
```powershell
# Check Docker is running
docker version

# Check ports are not in use
netstat -an | findstr "3000 8000 8001 8080"

# Force rebuild
docker-compose down -v
docker-compose up -d --build --force-recreate
```

### Database Issues:
```powershell
# Reset DynamoDB
docker-compose restart dynamodb-local
Start-Sleep -Seconds 10
python setup_local_db.py
```

### API Not Responding:
```powershell
# Check service logs
docker-compose logs conversion-engine

# Restart specific service
docker-compose restart conversion-engine
```

## 🔄 Stopping the Environment

```powershell
# Stop all services
docker-compose down

# Stop and remove all data
docker-compose down -v
```

## 💡 Tips for Development

1. **Use DynamoDB Admin** (http://localhost:8001) to inspect data
2. **Monitor logs** with `docker-compose logs -f` while testing
3. **Test error scenarios** to ensure robust error handling
4. **Verify audit trails** for compliance requirements
5. **Use browser DevTools** to debug frontend issues

## 📚 Next Steps

After successful local testing:
1. **Deploy to AWS** using the production infrastructure
2. **Set up CI/CD** with GitHub Actions
3. **Configure monitoring** and alerting
4. **Run load tests** for performance validation

---

**🎉 Happy Testing!** If you encounter any issues, check the logs and refer to this guide.