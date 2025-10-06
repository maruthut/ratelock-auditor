#!/usr/bin/env pwsh

Write-Host "Starting RateLock Local Development Environment" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green

Write-Host ""
Write-Host "Prerequisites Check:" -ForegroundColor Yellow

# Check Docker
try {
    $dockerVersion = docker --version
    Write-Host "Docker is available: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "Docker is not installed or not in PATH" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "Cleaning up any existing containers..." -ForegroundColor Yellow
docker-compose down -v

Write-Host ""
Write-Host "Building and starting services..." -ForegroundColor Yellow
docker-compose up -d --build

Write-Host ""
Write-Host "Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

Write-Host ""
Write-Host "Setting up DynamoDB tables..." -ForegroundColor Yellow

# Wait for DynamoDB to be ready
$maxAttempts = 10
$attempt = 1
do {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        # Any response (even error response) means DynamoDB is listening
        Write-Host "DynamoDB is ready" -ForegroundColor Green
        break
    } catch {
        # Check if it's just an authentication error (which means DynamoDB is working)
        if ($_.Exception.Response.StatusCode -eq 400) {
            Write-Host "DynamoDB is ready" -ForegroundColor Green
            break
        }
        Write-Host "Waiting for DynamoDB... (attempt $attempt/$maxAttempts)" -ForegroundColor Yellow
        Start-Sleep -Seconds 3
    }
    $attempt++
} while ($attempt -le $maxAttempts)

if ($attempt -gt $maxAttempts) {
    Write-Host "DynamoDB failed to start" -ForegroundColor Red
    exit 1
}

# Setup tables
python setup_local_db.py

Write-Host ""
Write-Host "Waiting for services to initialize and sync rates..." -ForegroundColor Yellow
Start-Sleep -Seconds 30

Write-Host ""
Write-Host "Running initial tests..." -ForegroundColor Yellow
python test_local.py

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "RateLock Local Environment is Ready!" -ForegroundColor Green
Write-Host ""

Write-Host "Frontend:           http://localhost:3000" -ForegroundColor Cyan
Write-Host "API:                http://localhost:8080" -ForegroundColor Cyan
Write-Host "DynamoDB Admin:     http://localhost:8001" -ForegroundColor Cyan
Write-Host ""

Write-Host "Useful Commands:" -ForegroundColor Yellow
Write-Host "   docker-compose logs -f           # View logs" -ForegroundColor Gray
Write-Host "   docker-compose ps                # Check status" -ForegroundColor Gray
Write-Host "   docker-compose down              # Stop services" -ForegroundColor Gray
Write-Host "   python test_local.py             # Run tests" -ForegroundColor Gray
Write-Host ""

Read-Host "Press Enter to continue"