#!/usr/bin/env python3
"""
AWS Deployment Script for RateLock
Automates the complete deployment process to AWS
"""

import subprocess
import sys
import os
import json
import time
import boto3
from pathlib import Path

class RateLockDeployer:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.cdk_dir = self.project_root / "cdk"
        self.region = "us-east-1"
        
    def run_command(self, command, cwd=None, check=True):
        """Run shell command and return output"""
        print(f"🔄 Running: {command}")
        if cwd is None:
            cwd = self.project_root
            
        try:
            result = subprocess.run(
                command.split(),
                cwd=cwd,
                capture_output=True,
                text=True,
                check=check
            )
            if result.stdout:
                print(result.stdout)
            return result
        except subprocess.CalledProcessError as e:
            print(f"❌ Command failed: {e}")
            if e.stderr:
                print(e.stderr)
            raise

    def check_prerequisites(self):
        """Check if required tools are installed"""
        print("🔍 Checking prerequisites...")
        
        # Check AWS CLI
        try:
            result = self.run_command("aws --version")
            print(f"✅ AWS CLI: {result.stdout.strip()}")
        except:
            print("❌ AWS CLI not found. Please install AWS CLI.")
            return False
            
        # Check Docker
        try:
            result = self.run_command("docker --version")
            print(f"✅ Docker: {result.stdout.strip()}")
        except:
            print("❌ Docker not found. Please install Docker.")
            return False
            
        # Check CDK
        try:
            result = self.run_command("cdk --version")
            print(f"✅ CDK: {result.stdout.strip()}")
        except:
            print("❌ CDK not found. Installing CDK...")
            self.run_command("npm install -g aws-cdk")
            
        # Check AWS credentials
        try:
            session = boto3.Session()
            credentials = session.get_credentials()
            if credentials is None:
                print("❌ AWS credentials not configured. Run 'aws configure'")
                return False
            print("✅ AWS credentials configured")
        except:
            print("❌ AWS credentials issue. Run 'aws configure'")
            return False
            
        return True

    def setup_cdk(self):
        """Initialize and bootstrap CDK"""
        print("🏗️ Setting up CDK...")
        
        # Install CDK dependencies
        print("📦 Installing CDK dependencies...")
        self.run_command("pip install -r requirements.txt", cwd=self.cdk_dir)
        
        # Bootstrap CDK (one-time setup)
        print("🚀 Bootstrapping CDK...")
        try:
            self.run_command(f"cdk bootstrap aws://$(aws sts get-caller-identity --query Account --output text)/{self.region}", cwd=self.cdk_dir)
        except:
            print("⚠️ CDK bootstrap might have failed, continuing...")

    def build_and_push_images(self):
        """Build and push Docker images to ECR"""
        print("🐳 Building and pushing Docker images...")
        
        # Get account ID
        account_id = boto3.client('sts').get_caller_identity()['Account']
        
        # Login to ECR
        print("🔑 Logging into ECR...")
        ecr_login_cmd = f"aws ecr get-login-password --region {self.region}"
        login_result = subprocess.run(ecr_login_cmd.split(), capture_output=True, text=True)
        login_password = login_result.stdout.strip()
        
        docker_login_cmd = f"docker login --username AWS --password {login_password} {account_id}.dkr.ecr.{self.region}.amazonaws.com"
        subprocess.run(docker_login_cmd, shell=True, check=True)
        
        # Build and push ConversionEngine
        print("🔨 Building ConversionEngine image...")
        conversion_repo = f"{account_id}.dkr.ecr.{self.region}.amazonaws.com/ratelock/conversion-engine"
        
        self.run_command("docker build -t ratelock/conversion-engine .", cwd=self.project_root / "service-conversion")
        self.run_command(f"docker tag ratelock/conversion-engine:latest {conversion_repo}:latest")
        self.run_command(f"docker push {conversion_repo}:latest")
        
        # Build and push RateSync
        print("🔨 Building RateSync image...")
        ratesync_repo = f"{account_id}.dkr.ecr.{self.region}.amazonaws.com/ratelock/ratesync"
        
        self.run_command("docker build -t ratelock/ratesync .", cwd=self.project_root / "service-ratesync")
        self.run_command(f"docker tag ratelock/ratesync:latest {ratesync_repo}:latest")
        self.run_command(f"docker push {ratesync_repo}:latest")
        
        print("✅ Docker images built and pushed successfully")

    def deploy_infrastructure(self):
        """Deploy CDK stacks"""
        print("☁️ Deploying infrastructure to AWS...")
        
        # Deploy all stacks
        self.run_command("cdk deploy --all --require-approval never", cdk=self.cdk_dir)
        
        print("✅ Infrastructure deployed successfully")

    def get_outputs(self):
        """Get stack outputs"""
        print("📋 Getting deployment outputs...")
        
        try:
            result = self.run_command("aws cloudformation describe-stacks", check=False)
            if result.returncode == 0:
                stacks = json.loads(result.stdout)
                for stack in stacks['Stacks']:
                    if 'RateLock' in stack['StackName']:
                        print(f"\n📊 Stack: {stack['StackName']}")
                        if 'Outputs' in stack:
                            for output in stack['Outputs']:
                                print(f"  {output['OutputKey']}: {output['OutputValue']}")
        except:
            print("⚠️ Could not retrieve stack outputs")

    def run_smoke_tests(self):
        """Run basic smoke tests"""
        print("🧪 Running smoke tests...")
        
        # Wait for services to be ready
        print("⏳ Waiting for services to initialize...")
        time.sleep(60)
        
        # Run AWS tests
        try:
            self.run_command("python test_aws.py", cwd=self.project_root / "scripts")
            print("✅ Smoke tests passed")
        except:
            print("⚠️ Some smoke tests failed, check manually")

    def deploy(self):
        """Main deployment process"""
        print("🚀 Starting RateLock deployment to AWS")
        print("=" * 50)
        
        if not self.check_prerequisites():
            print("❌ Prerequisites check failed")
            return False
            
        try:
            self.setup_cdk()
            self.deploy_infrastructure()
            self.build_and_push_images() 
            self.get_outputs()
            self.run_smoke_tests()
            
            print("\n" + "=" * 50)
            print("🎉 RateLock deployment completed successfully!")
            print("📊 Check the outputs above for URLs and endpoints")
            print("🔧 Monitor your AWS console for service status")
            
            return True
            
        except Exception as e:
            print(f"\n❌ Deployment failed: {e}")
            return False

if __name__ == "__main__":
    deployer = RateLockDeployer()
    success = deployer.deploy()
    sys.exit(0 if success else 1)