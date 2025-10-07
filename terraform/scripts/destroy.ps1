#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Destroy RateLock infrastructure

.DESCRIPTION
    This script safely destroys the RateLock infrastructure using Terraform.
    It includes confirmation prompts to prevent accidental destruction.

.PARAMETER Environment
    The environment to destroy (dev, staging, prod)

.PARAMETER Force
    Skip confirmation prompts (use with caution!)

.EXAMPLE
    .\destroy.ps1 -Environment dev
    Destroy the development environment with confirmation

.EXAMPLE
    .\destroy.ps1 -Environment dev -Force
    Destroy the development environment without confirmation (dangerous!)
#>

param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("dev", "staging", "prod")]
    [string]$Environment,
    
    [Parameter(Mandatory = $false)]
    [switch]$Force
)

# Set error action preference
$ErrorActionPreference = "Stop"

# Get script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$TerraformDir = Split-Path -Parent $ScriptDir
$EnvironmentDir = Join-Path $TerraformDir "environments\$Environment"

Write-Host "🗑️  RateLock Infrastructure Destruction" -ForegroundColor Red
Write-Host "Environment: $Environment" -ForegroundColor Yellow
Write-Host "⚠️  WARNING: This will destroy ALL infrastructure in the $Environment environment!" -ForegroundColor Red

# Safety checks
if ($Environment -eq "prod" -and -not $Force) {
    Write-Host "❌ Production environment destruction requires -Force flag" -ForegroundColor Red
    Write-Host "This is a safety measure to prevent accidental production destruction." -ForegroundColor Yellow
    exit 1
}

if (-not $Force) {
    $Confirmation1 = Read-Host "Type the environment name '$Environment' to confirm"
    if ($Confirmation1 -ne $Environment) {
        Write-Host "❌ Environment name confirmation failed. Destruction cancelled." -ForegroundColor Red
        exit 1
    }
    
    $Confirmation2 = Read-Host "Are you absolutely sure you want to destroy the $Environment environment? (yes/no)"
    if ($Confirmation2 -ne "yes") {
        Write-Host "❌ Destruction cancelled by user" -ForegroundColor Yellow
        exit 0
    }
}

# Check if environment directory exists
if (-not (Test-Path $EnvironmentDir)) {
    Write-Error "❌ Environment directory not found: $EnvironmentDir"
    exit 1
}

Set-Location $EnvironmentDir

# Check if Terraform state exists
if (-not (Test-Path "terraform.tfstate")) {
    Write-Host "⚠️  No Terraform state found. Nothing to destroy." -ForegroundColor Yellow
    exit 0
}

# Initialize Terraform
Write-Host "🔧 Initializing Terraform..." -ForegroundColor Cyan
try {
    terraform init
    Write-Host "✅ Terraform initialized successfully" -ForegroundColor Green
} catch {
    Write-Error "❌ Terraform initialization failed"
    exit 1
}

# Show what will be destroyed
Write-Host "📋 Generating destruction plan..." -ForegroundColor Cyan
try {
    terraform plan -destroy
} catch {
    Write-Error "❌ Failed to generate destruction plan"
    exit 1
}

# Final confirmation
if (-not $Force) {
    $FinalConfirmation = Read-Host "Proceed with destruction? (yes/no)"
    if ($FinalConfirmation -ne "yes") {
        Write-Host "❌ Destruction cancelled by user" -ForegroundColor Yellow
        exit 0
    }
}

# Destroy infrastructure
Write-Host "🗑️  Destroying infrastructure..." -ForegroundColor Red
try {
    if ($Force) {
        terraform destroy -auto-approve
    } else {
        terraform destroy
    }
    Write-Host "✅ Infrastructure destroyed successfully" -ForegroundColor Green
} catch {
    Write-Error "❌ Infrastructure destruction failed"
    exit 1
}

Write-Host "🎉 Destruction completed successfully!" -ForegroundColor Green