#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Deploy RateLock infrastructure using Terraform

.DESCRIPTION
    This script deploys the RateLock application infrastructure to AWS using Terraform.
    It supports deploying specific components or the entire stack.

.PARAMETER Environment
    The environment to deploy to (dev, staging, prod)

.PARAMETER Component
    Optional. Deploy only a specific component (database, compute, api, frontend)
    If not specified, deploys all components

.PARAMETER AutoApprove
    Skip interactive approval of Terraform plan

.PARAMETER Destroy
    Destroy the infrastructure instead of creating it

.EXAMPLE
    .\deploy.ps1 -Environment dev
    Deploy the entire development environment

.EXAMPLE
    .\deploy.ps1 -Environment dev -Component database
    Deploy only the database component for development

.EXAMPLE
    .\deploy.ps1 -Environment dev -AutoApprove
    Deploy development environment without interactive approval
#>

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("dev", "staging", "prod")]
    [string]$Environment,
    
    [Parameter(Mandatory = $false)]
    [ValidateSet("database", "compute", "api", "frontend")]
    [string]$Component,
    
    [Parameter(Mandatory = $false)]
    [switch]$AutoApprove,
    
    [Parameter(Mandatory = $false)]
    [switch]$Destroy
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TerraformDir = Split-Path -Parent $ScriptDir
$EnvironmentDir = Join-Path $TerraformDir "environments\$Environment"

Write-Host "🚀 RateLock Infrastructure Deployment" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Yellow
Write-Host "Directory: $EnvironmentDir" -ForegroundColor Yellow

# Check if Terraform is installed
try {
    $TerraformVersion = terraform version
    Write-Host "✅ Terraform found: $($TerraformVersion[0])" -ForegroundColor Green
} catch {
    Write-Error "❌ Terraform not found. Please install Terraform: https://developer.hashicorp.com/terraform/downloads"
    exit 1
}

# Check if AWS CLI is configured
try {
    $AWSAccount = aws sts get-caller-identity --query Account --output text
    Write-Host "✅ AWS CLI configured for account: $AWSAccount" -ForegroundColor Green
} catch {
    Write-Error "❌ AWS CLI not configured. Please run 'aws configure' first."
    exit 1
}

# Navigate to environment directory
if (-not (Test-Path $EnvironmentDir)) {
    Write-Error "❌ Environment directory not found: $EnvironmentDir"
    exit 1
}

Set-Location $EnvironmentDir
Write-Host "📁 Working in: $(Get-Location)" -ForegroundColor Cyan

# Initialize Terraform
Write-Host "🔧 Initializing Terraform..." -ForegroundColor Cyan
try {
    terraform init
    Write-Host "✅ Terraform initialized successfully" -ForegroundColor Green
} catch {
    Write-Error "❌ Terraform initialization failed"
    exit 1
}

# Validate Terraform configuration
Write-Host "🔍 Validating Terraform configuration..." -ForegroundColor Cyan
try {
    terraform validate
    Write-Host "✅ Terraform configuration is valid" -ForegroundColor Green
} catch {
    Write-Error "❌ Terraform configuration validation failed"
    exit 1
}

# Format Terraform files
Write-Host "📝 Formatting Terraform files..." -ForegroundColor Cyan
terraform fmt -recursive

# Generate and show plan
Write-Host "📋 Generating Terraform plan..." -ForegroundColor Cyan
try {
    if ($Destroy) {
        terraform plan -destroy -out=tfplan
    } else {
        terraform plan -out=tfplan
    }
    Write-Host "✅ Terraform plan generated successfully" -ForegroundColor Green
} catch {
    Write-Error "❌ Terraform plan generation failed"
    exit 1
}

# Apply plan
if (-not $AutoApprove) {
    $Confirmation = Read-Host "Do you want to apply this plan? (yes/no)"
    if ($Confirmation -ne "yes") {
        Write-Host "❌ Deployment cancelled by user" -ForegroundColor Yellow
        Remove-Item tfplan -ErrorAction SilentlyContinue
        exit 0
    }
}

Write-Host "🚀 Applying Terraform plan..." -ForegroundColor Cyan
try {
    terraform apply tfplan
    Write-Host "✅ Terraform apply completed successfully" -ForegroundColor Green
} catch {
    Write-Error "❌ Terraform apply failed"
    exit 1
} finally {
    # Clean up plan file
    Remove-Item tfplan -ErrorAction SilentlyContinue
}

# Show outputs
if (-not $Destroy) {
    Write-Host "📊 Deployment Summary:" -ForegroundColor Cyan
    terraform output -json | ConvertFrom-Json | Format-Table -AutoSize
    
    Write-Host "🎉 Deployment completed successfully!" -ForegroundColor Green
    Write-Host "You can check the application at the URL shown above." -ForegroundColor Cyan
} else {
    Write-Host "🗑️ Infrastructure destroyed successfully!" -ForegroundColor Green
}