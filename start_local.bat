@echo off
echo 🚀 Starting RateLock Local Development Environment
echo ================================================

echo.
echo 📋 Prerequisites Check:
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed or not in PATH
    pause
    exit /b 1
)
echo ✅ Docker is available

echo.
echo 🧹 Cleaning up any existing containers...
docker-compose down -v

echo.
echo 🏗️ Building and starting services...
docker-compose up -d --build

echo.
echo ⏳ Waiting for services to be ready...
timeout /t 15 /nobreak >nul

echo.
echo 🔧 Setting up DynamoDB tables...
docker-compose exec -T dynamodb-local sh -c "curl -s http://localhost:8000 >/dev/null" 2>nul
if %errorlevel% neq 0 (
    echo ⚠️ DynamoDB not ready yet, waiting longer...
    timeout /t 10 /nobreak >nul
)

python setup_local_db.py

echo.
echo 🧪 Running initial tests...
python test_local.py

echo.
echo ================================================
echo 🎉 RateLock Local Environment is Ready!
echo.
echo 📱 Frontend:           http://localhost:3000
echo 🔧 API:                http://localhost:8080
echo 📊 DynamoDB Admin:     http://localhost:8001
echo.
echo 💡 Useful Commands:
echo    docker-compose logs -f           # View logs
echo    docker-compose ps                # Check status
echo    docker-compose down              # Stop services
echo    python test_local.py             # Run tests
echo.
pause