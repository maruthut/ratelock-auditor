# Deploy to AWS PowerShell Script
# Deploys RateLock to AWS using CDK

Write-Host "☁️ Deploying RateLock to AWS..." -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Change to project directory
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

# Check prerequisites
Write-Host "🔍 Checking prerequisites..." -ForegroundColor Yellow

# Check if AWS CLI is installed
try {
    $awsVersion = aws --version 2>&1
    Write-Host "✅ AWS CLI: $awsVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ AWS CLI not found. Please install AWS CLI first." -ForegroundColor Red
    exit 1
}

# Check if Docker is running
try {
    $dockerVersion = docker --version 2>&1
    Write-Host "✅ Docker: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker not found. Please install Docker first." -ForegroundColor Red
    exit 1
}

# Check if CDK is installed
try {
    $cdkVersion = cdk --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "CDK command failed"
    }
    Write-Host "✅ CDK: $cdkVersion" -ForegroundColor Green
} catch {
    Write-Host "⚠️ CDK not found. Installing CDK..." -ForegroundColor Yellow
    try {
        npm install -g aws-cdk
        if ($LASTEXITCODE -ne 0) {
            throw "NPM install failed"
        }
        Write-Host "✅ CDK installed successfully" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to install CDK. Please install Node.js and npm first." -ForegroundColor Red
        exit 1
    }
}

# Check AWS credentials
try {
    $identity = aws sts get-caller-identity 2>&1 | ConvertFrom-Json
    $accountId = $identity.Account
    Write-Host "✅ AWS credentials configured (Account: $accountId)" -ForegroundColor Green
} catch {
    Write-Host "❌ AWS credentials not configured. Run 'aws configure' first." -ForegroundColor Red
    Write-Host "   Or set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables." -ForegroundColor Yellow
    exit 1
}

# Run Python deployment script
Write-Host "🚀 Starting deployment..." -ForegroundColor Cyan
python scripts\deploy_aws.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "🎉 Deployment completed successfully!" -ForegroundColor Green
    Write-Host "📊 Check the output above for URLs and endpoints" -ForegroundColor Cyan
} else {
    Write-Host "❌ Deployment failed. Check the logs above." -ForegroundColor Red
    exit 1
}