#!/usr/bin/env python3
"""
AWS Testing Script for RateLock
Tests the deployed AWS infrastructure and services
"""

import requests
import json
import time
import sys
import boto3
from datetime import datetime

class RateLockAWSTest:
    def __init__(self):
        self.api_base_url = None
        self.website_url = None
        self.load_config()
    
    def load_config(self):
        """Load configuration from CloudFormation outputs"""
        print("🔍 Loading configuration from AWS...")
        
        try:
            cf_client = boto3.client('cloudformation')
            stacks = cf_client.describe_stacks()
            
            for stack in stacks['Stacks']:
                if 'RateLock' in stack['StackName'] and 'Outputs' in stack:
                    for output in stack['Outputs']:
                        if output['OutputKey'] == 'ApiGatewayUrl':
                            self.api_base_url = output['OutputValue'].rstrip('/')
                        elif output['OutputKey'] == 'WebsiteUrl':
                            self.website_url = output['OutputValue']
            
            if not self.api_base_url:
                print("❌ Could not find API Gateway URL in CloudFormation outputs")
                return False
                
            print(f"✅ API Base URL: {self.api_base_url}")
            if self.website_url:
                print(f"✅ Website URL: {self.website_url}")
                
            return True
            
        except Exception as e:
            print(f"❌ Failed to load configuration: {e}")
            return False

    def test_api_health(self):
        """Test API health endpoint"""
        print("\n🔍 Testing API health...")
        
        try:
            response = requests.get(f"{self.api_base_url}/health", timeout=10)
            if response.status_code == 200:
                data = response.json()
                print(f"✅ API Health: {data.get('status', 'unknown')}")
                print(f"   Service: {data.get('service', 'unknown')}")
                return True
            else:
                print(f"❌ API Health failed: Status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ API Health test failed: {e}")
            return False

    def test_currency_conversion(self):
        """Test currency conversion functionality"""
        print("\n💱 Testing currency conversion...")
        
        test_cases = [
            {"from": "USD", "to": "EUR", "amount": "100"},
            {"from": "EUR", "to": "GBP", "amount": "50"},
            {"from": "USD", "to": "USD", "amount": "100"},  # Same currency
        ]
        
        conversion_results = []
        
        for i, test_case in enumerate(test_cases, 1):
            print(f"  Test {i}: {test_case['amount']} {test_case['from']} → {test_case['to']}")
            
            try:
                response = requests.get(
                    f"{self.api_base_url}/v1/convert",
                    params=test_case,
                    timeout=15
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"    ✅ Result: {data['converted_amount']} {test_case['to']}")
                    print(f"    📋 Snapshot: {data.get('rate_snapshot_id', 'N/A')}")
                    print(f"    🔍 Audit: {data.get('audit_log_transaction_id', 'N/A')}")
                    conversion_results.append(data)
                else:
                    print(f"    ❌ Failed: Status {response.status_code}")
                    if response.headers.get('content-type', '').startswith('application/json'):
                        error_data = response.json()
                        print(f"    📝 Error: {error_data.get('detail', 'Unknown error')}")
                        
            except Exception as e:
                print(f"    ❌ Request failed: {e}")
        
        return conversion_results

    def test_audit_retrieval(self, conversion_results):
        """Test audit record retrieval"""
        print("\n🔍 Testing audit record retrieval...")
        
        if not conversion_results:
            print("    ⚠️ No conversion results to test audit retrieval")
            return
        
        for i, result in enumerate(conversion_results, 1):
            transaction_id = result.get('audit_log_transaction_id')
            if not transaction_id:
                print(f"    ⚠️ Test {i}: No transaction ID available")
                continue
            
            print(f"  Test {i}: Retrieving {transaction_id}")
            
            try:
                response = requests.get(
                    f"{self.api_base_url}/v1/audit/{transaction_id}",
                    timeout=10
                )
                
                if response.status_code == 200:
                    audit_data = response.json()
                    print(f"    ✅ Audit record retrieved")
                    print(f"    📅 Timestamp: {audit_data.get('ConversionTimestamp', 'N/A')}")
                    print(f"    💰 Amount: {audit_data.get('OriginalAmount', 'N/A')} {audit_data.get('FromCurrency', 'N/A')}")
                else:
                    print(f"    ❌ Failed: Status {response.status_code}")
                    
            except Exception as e:
                print(f"    ❌ Request failed: {e}")

    def test_error_handling(self):
        """Test error handling scenarios"""
        print("\n🚨 Testing error handling...")
        
        error_test_cases = [
            {"from": "USD", "to": "EUR", "amount": "invalid", "expected": "validation"},
            {"from": "INVALID", "to": "EUR", "amount": "100", "expected": "validation"},
            {"from": "USD", "to": "", "amount": "100", "expected": "validation"},
        ]
        
        for i, test_case in enumerate(error_test_cases, 1):
            expected_error = test_case.pop('expected')
            print(f"  Error Test {i}: {test_case} (expecting: {expected_error})")
            
            try:
                response = requests.get(
                    f"{self.api_base_url}/v1/convert",
                    params=test_case,
                    timeout=10
                )
                
                if response.status_code != 200:
                    print(f"    ✅ Error handled correctly: Status {response.status_code}")
                else:
                    print(f"    ⚠️ Expected error but got success")
                    
            except Exception as e:
                print(f"    ❌ Request failed: {e}")

    def test_website_access(self):
        """Test website accessibility"""
        print("\n🌐 Testing website access...")
        
        if not self.website_url:
            print("    ⚠️ Website URL not available")
            return
        
        try:
            response = requests.get(self.website_url, timeout=10)
            if response.status_code == 200:
                print(f"✅ Website accessible at {self.website_url}")
                return True
            else:
                print(f"❌ Website failed: Status {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Website test failed: {e}")
            return False

    def test_rate_information(self):
        """Test rate information endpoint"""
        print("\n📊 Testing rate information...")
        
        try:
            response = requests.get(f"{self.api_base_url}/v1/rates", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                print(f"    ✅ Rate info retrieved")
                print(f"    📋 Snapshot: {data.get('rate_snapshot_id', 'N/A')}")
                print(f"    🏦 Base: {data.get('base_currency', 'N/A')}")
                print(f"    📈 Count: {data.get('rates_count', 'N/A')}")
                return True
            else:
                print(f"    ❌ Failed: Status {response.status_code}")
                return False
                
        except Exception as e:
            print(f"    ❌ Request failed: {e}")
            return False

    def run_all_tests(self):
        """Run all tests"""
        print("🚀 Starting AWS Tests for RateLock")
        print("=" * 50)
        
        if not self.load_config():
            return False
        
        # Wait for services to be ready
        print("\n⏳ Waiting for services to be fully ready...")
        time.sleep(30)
        
        test_results = []
        
        # Run tests
        test_results.append(self.test_api_health())
        test_results.append(self.test_rate_information())
        
        conversion_results = self.test_currency_conversion()
        test_results.append(len(conversion_results) > 0)
        
        self.test_audit_retrieval(conversion_results)
        self.test_error_handling()
        test_results.append(self.test_website_access())
        
        # Summary
        passed = sum(test_results)
        total = len(test_results)
        
        print("\n" + "=" * 50)
        print(f"🎉 AWS Testing Complete: {passed}/{total} tests passed")
        
        if self.api_base_url:
            print(f"📡 API Endpoint: {self.api_base_url}")
        if self.website_url:
            print(f"🌐 Website: {self.website_url}")
        
        return passed == total

if __name__ == "__main__":
    tester = RateLockAWSTest()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)