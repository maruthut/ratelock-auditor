#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Check the status of RateLock infrastructure

.DESCRIPTION
    This script checks the status of the RateLock infrastructure deployment,
    showing current resources and their states.

.PARAMETER Environment
    The environment to check (dev, staging, prod)

.EXAMPLE
    .\status.ps1 -Environment dev
    Check the status of the development environment
#>

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("dev", "staging", "prod")]
    [string]$Environment
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TerraformDir = Split-Path -Parent $ScriptDir
$EnvironmentDir = Join-Path $TerraformDir "environments\$Environment"

Write-Host "📊 RateLock Infrastructure Status" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Yellow

# Check if environment directory exists
if (-not (Test-Path $EnvironmentDir)) {
    Write-Error "❌ Environment directory not found: $EnvironmentDir"
    exit 1
}

Set-Location $EnvironmentDir

# Check if Terraform state exists
if (-not (Test-Path "terraform.tfstate")) {
    Write-Host "⚠️  No Terraform state found. Infrastructure may not be deployed." -ForegroundColor Yellow
    exit 0
}

Write-Host "🔍 Terraform State:" -ForegroundColor Cyan
try {
    terraform show -json | ConvertFrom-Json | Select-Object -ExpandProperty values | 
        Select-Object -ExpandProperty root_module | Select-Object -ExpandProperty resources |
        Select-Object address, type, name | Format-Table -AutoSize
} catch {
    Write-Host "⚠️  Could not parse Terraform state" -ForegroundColor Yellow
}

Write-Host "📋 Current Outputs:" -ForegroundColor Cyan
try {
    terraform output
} catch {
    Write-Host "⚠️  No outputs found or Terraform not initialized" -ForegroundColor Yellow
}

Write-Host "☁️  AWS Resources:" -ForegroundColor Cyan
try {
    # Check DynamoDB tables
    Write-Host "DynamoDB Tables:" -ForegroundColor Yellow
    aws dynamodb list-tables --query "TableNames[?contains(@, 'ratelock')]" --output table
    
    # Check ECS clusters
    Write-Host "ECS Clusters:" -ForegroundColor Yellow
    aws ecs list-clusters --query "clusterArns[?contains(@, 'ratelock')]" --output table
    
    # Check Load Balancers
    Write-Host "Load Balancers:" -ForegroundColor Yellow
    aws elbv2 describe-load-balancers --query "LoadBalancers[?contains(LoadBalancerName, 'ratelock')].{Name:LoadBalancerName, DNS:DNSName, State:State.Code}" --output table
    
    # Check ECR repositories
    Write-Host "ECR Repositories:" -ForegroundColor Yellow
    aws ecr describe-repositories --query "repositories[?contains(repositoryName, 'ratelock')].{Name:repositoryName, URI:repositoryUri}" --output table
    
} catch {
    Write-Host "⚠️  Could not retrieve AWS resource information" -ForegroundColor Yellow
}

Write-Host "✅ Status check completed" -ForegroundColor Green