# RateLock - Auditable Currency Conversion API

[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue)](https://github.com/maruthut/ratelock-auditor)

## 🎯 Project Overview

RateLock is a **high-speed, auditable currency conversion service** designed to solve the financial compliance problem of **Audit and Compliance Risk**. Instead of relying on expensive, volatile real-time market data, RateLock provides consistent, fixed hourly exchange rates with complete audit trails.

### 🔐 Key Value Proposition
- **Immutable audit records** for every conversion
- **Regulatory compliance** for invoicing, payroll, and financial reporting
- **Cost-optimized** rate caching with automatic cleanup
- **High-speed API** with sub-second response times
- **AWS-native architecture** for scalability and reliability

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │    │   API Gateway    │    │   CloudFront    │
│   (S3 Static)   │◄───┤   (Rate Limit)   │◄───┤   (Global CDN)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
            ┌─────────────────────────────────────────┐
            │           ECS Fargate Cluster           │
            │  ┌─────────────────┐ ┌─────────────────┐│
            │  │   RateSync      │ │ ConversionEngine││
            │  │   (Worker)      │ │    (API)        ││
            │  └─────────────────┘ └─────────────────┘│
            └─────────────────────────────────────────┘
                                │
                                ▼
            ┌─────────────────────────────────────────┐
            │              DynamoDB                   │
            │  ┌─────────────────┐ ┌─────────────────┐│
            │  │ RateCacheTable  │ │ConversionAudit  ││
            │  │   (TTL: 30d)    │ │ LogTable (∞)    ││
            │  └─────────────────┘ └─────────────────┘│
            └─────────────────────────────────────────┘
```

## 🚀 Services

### 1. **RateSync Service** (Microservice 1)
- **Purpose**: Asynchronous worker for rate synchronization
- **Trigger**: Hourly schedule via EventBridge
- **Data Source**: [Frankfurter API](https://frankfurter.app/) (European Central Bank)
- **Output**: Timestamped rate snapshots in DynamoDB

**Key Features:**
- ✅ Unique snapshot IDs (`YYYYMMDD-HHMMUTC`)
- ✅ Retry logic with exponential backoff
- ✅ Duplicate prevention
- ✅ TTL-based automatic cleanup (30 days)

### 2. **ConversionEngine Service** (Microservice 2)
- **Purpose**: High-speed customer-facing conversion API
- **Access**: Public via API Gateway
- **Method**: EUR-based triangulation for all currency pairs
- **Audit**: Immutable log for every conversion

**Key Features:**
- ✅ Sub-second response times
- ✅ Decimal precision for financial accuracy
- ✅ CORS enabled for frontend integration
- ✅ Comprehensive error handling
- ✅ Rate validation before conversion

### 3. **Frontend Application**
- **Technology**: Single-page HTML/CSS/JavaScript
- **Hosting**: S3 Static Website + CloudFront
- **Features**: Professional UI with audit trail display

## 📊 API Endpoints

### Public Endpoints

#### `GET /v1/convert`
Convert currency amounts with full audit logging.

**Parameters:**
- `from`: Source currency code (3 chars)
- `to`: Target currency code (3 chars)  
- `amount`: Amount to convert (positive number)

**Response:**
```json
{
  "converted_amount": 123.45,
  "rate_snapshot_id": "20251004-1400UTC",
  "audit_log_transaction_id": "audit-1728054000-a1b2c3d4",
  "from_currency": "USD",
  "to_currency": "EUR",
  "original_amount": 100.00,
  "conversion_timestamp": "2025-10-04T14:00:00Z"
}
```

### Internal Endpoints

#### `GET /v1/audit/{transactionId}`
Retrieve complete audit record for compliance verification.

#### `GET /health`
Service health check endpoint.

## 🛡️ Audit & Compliance

### Rate Snapshot System
Every hour, RateSync creates a **Rate Snapshot** with:
- Unique timestamp-based ID
- Complete set of EUR-based rates
- Immutable storage with audit trail

### Conversion Audit Log
Every conversion creates an **Audit Record** containing:
- Original conversion request
- Rate Snapshot ID used
- Calculation method (triangulation/direct)
- Timestamp and transaction ID
- **Permanent retention** for regulatory compliance

### Auditable Guarantee
The `rate_snapshot_id` in the audit log permanently links each conversion to the official rate used, making it **defensible to auditors** and **compliant with financial regulations**.

## 🚀 Deployment

### Prerequisites
- AWS Account with appropriate permissions
- Docker for containerization
- Terraform or CloudFormation for infrastructure

### Local Development
```bash
# Clone the repository
git clone https://github.com/maruthut/ratelock-auditor.git
cd ratelock-auditor

# Build and run RateSync service
cd service-ratesync
docker build -t ratelock-ratesync .
docker run -e RATE_CACHE_TABLE=RateCacheTable ratelock-ratesync

# Build and run ConversionEngine service
cd ../service-conversion
docker build -t ratelock-conversion .
docker run -p 8080:8080 -e RATE_CACHE_TABLE=RateCacheTable -e AUDIT_LOG_TABLE=ConversionAuditLogTable ratelock-conversion
```

### AWS Deployment
1. **DynamoDB Tables**: Create `RateCacheTable` and `ConversionAuditLogTable`
2. **ECS Fargate**: Deploy both microservices as containers
3. **API Gateway**: Configure public endpoints with rate limiting
4. **EventBridge**: Schedule RateSync service execution
5. **S3 + CloudFront**: Deploy frontend application

## 💰 Cost Optimization

- **Rate Caching**: 30-day TTL reduces DynamoDB costs
- **Efficient Queries**: Limited scan operations
- **Fargate Scaling**: Pay-per-use container execution
- **Free Data Source**: Frankfurter API (no licensing costs)

## 🔧 Recent Improvements

### Code Review Fixes Applied:
✅ **Added CORS support** for frontend-backend communication  
✅ **Enhanced error handling** with comprehensive validation  
✅ **Improved rate retrieval** with scan limits and validation  
✅ **Added retry logic** with exponential backoff  
✅ **Prevented duplicate snapshots** with existence checks  
✅ **Fixed Docker health checks** with curl installation  
✅ **Enhanced input validation** for security and reliability  

## 📋 Development Status

- ✅ **Core Architecture**: Complete microservices implementation
- ✅ **Frontend**: Professional UI with audit trail display
- ✅ **Docker**: Production-ready containers
- ✅ **Code Quality**: Comprehensive error handling and logging
- 🔄 **Infrastructure**: AWS CloudFormation/Terraform templates (next phase)
- 🔄 **CI/CD**: GitHub Actions deployment pipeline (next phase)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Support

For questions or support, please open an issue in the [GitHub repository](https://github.com/maruthut/ratelock-auditor/issues).

---

**Built with ❤️ for financial compliance and audit transparency**