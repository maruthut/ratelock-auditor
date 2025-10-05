#!/usr/bin/env python3
"""
Test script for RateLock local deployment
Tests the complete end-to-end functionality
"""

import requests
import json
import time
import sys
from datetime import datetime

# Configuration
CONVERSION_API_URL = "http://localhost:8080"
FRONTEND_URL = "http://localhost:3000"
DYNAMODB_ADMIN_URL = "http://localhost:8001"

def test_service_health():
    """Test if all services are healthy"""
    print("🔍 Testing service health...")
    
    services = [
        ("ConversionEngine API", f"{CONVERSION_API_URL}/health"),
        ("Frontend", FRONTEND_URL),
        ("DynamoDB Admin", DYNAMODB_ADMIN_URL)
    ]
    
    for service_name, url in services:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                print(f"✅ {service_name}: Healthy")
            else:
                print(f"⚠️ {service_name}: Status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {service_name}: Failed - {e}")
            return False
    
    return True

def test_currency_conversion():
    """Test currency conversion functionality"""
    print("\n💱 Testing currency conversion...")
    
    test_cases = [
        {"from": "USD", "to": "EUR", "amount": "100"},
        {"from": "EUR", "to": "GBP", "amount": "50"},
        {"from": "GBP", "to": "JPY", "amount": "25"},
        {"from": "USD", "to": "USD", "amount": "100"},  # Same currency test
    ]
    
    conversion_results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n  Test {i}: Converting {test_case['amount']} {test_case['from']} to {test_case['to']}")
        
        try:
            response = requests.get(
                f"{CONVERSION_API_URL}/v1/convert",
                params=test_case,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"    ✅ Result: {data['converted_amount']} {test_case['to']}")
                print(f"    📋 Snapshot ID: {data.get('rate_snapshot_id', 'N/A')}")
                print(f"    🔍 Audit ID: {data.get('audit_log_transaction_id', 'N/A')}")
                conversion_results.append(data)
            else:
                print(f"    ❌ Failed: Status {response.status_code}")
                if response.headers.get('content-type', '').startswith('application/json'):
                    error_data = response.json()
                    print(f"    📝 Error: {error_data.get('error', 'Unknown error')}")
        except requests.exceptions.RequestException as e:
            print(f"    ❌ Request failed: {e}")
    
    return conversion_results

def test_audit_retrieval(conversion_results):
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
        
        print(f"\n  Test {i}: Retrieving audit record {transaction_id}")
        
        try:
            response = requests.get(
                f"{CONVERSION_API_URL}/v1/audit/{transaction_id}",
                timeout=10
            )
            
            if response.status_code == 200:
                audit_data = response.json()
                print(f"    ✅ Audit record retrieved successfully")
                print(f"    📅 Timestamp: {audit_data.get('ConversionTimestamp', 'N/A')}")
                print(f"    💰 Original: {audit_data.get('OriginalAmount', 'N/A')} {audit_data.get('FromCurrency', 'N/A')}")
                print(f"    💱 Converted: {audit_data.get('ConvertedAmount', 'N/A')} {audit_data.get('ToCurrency', 'N/A')}")
            else:
                print(f"    ❌ Failed: Status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"    ❌ Request failed: {e}")

def test_error_handling():
    """Test error handling scenarios"""
    print("\n🚨 Testing error handling...")
    
    error_test_cases = [
        {"from": "USD", "to": "EUR", "amount": "invalid", "expected": "Invalid amount"},
        {"from": "USD", "to": "EUR", "amount": "-100", "expected": "positive"},
        {"from": "INVALID", "to": "EUR", "amount": "100", "expected": "not supported"},
        {"from": "USD", "to": "", "amount": "100", "expected": "Missing"},
        {"from": "", "to": "EUR", "amount": "100", "expected": "Missing"},
    ]
    
    for i, test_case in enumerate(error_test_cases, 1):
        expected_error = test_case.pop('expected')
        print(f"\n  Error Test {i}: {test_case} (expecting: {expected_error})")
        
        try:
            response = requests.get(
                f"{CONVERSION_API_URL}/v1/convert",
                params=test_case,
                timeout=10
            )
            
            if response.status_code != 200:
                error_data = response.json() if response.headers.get('content-type', '').startswith('application/json') else {}
                error_msg = error_data.get('error', 'Unknown error')
                print(f"    ✅ Error handled correctly: {error_msg}")
            else:
                print(f"    ⚠️ Expected error but got success")
        except requests.exceptions.RequestException as e:
            print(f"    ❌ Request failed: {e}")

def test_rate_snapshot_info():
    """Test rate snapshot information endpoint"""
    print("\n📊 Testing rate snapshot information...")
    
    try:
        response = requests.get(f"{CONVERSION_API_URL}/v1/rates", timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            print(f"    ✅ Rate snapshot info retrieved")
            print(f"    📋 Snapshot ID: {data.get('rate_snapshot_id', 'N/A')}")
            print(f"    🏦 Base Currency: {data.get('base_currency', 'N/A')}")
            print(f"    📈 Rates Count: {data.get('rates_count', 'N/A')}")
            print(f"    🕐 Fetch Time: {data.get('fetch_timestamp', 'N/A')}")
        else:
            print(f"    ❌ Failed: Status {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"    ❌ Request failed: {e}")

def main():
    """Run all tests"""
    print("🚀 Starting RateLock Local Testing Suite")
    print("=" * 50)
    
    # Test service health
    if not test_service_health():
        print("\n❌ Service health check failed. Make sure all services are running.")
        print("Run: docker-compose up -d")
        sys.exit(1)
    
    # Wait a bit for services to be fully ready
    print("\n⏳ Waiting for services to be fully ready...")
    time.sleep(5)
    
    # Test rate snapshot info first
    test_rate_snapshot_info()
    
    # Test currency conversions
    conversion_results = test_currency_conversion()
    
    # Test audit retrieval
    test_audit_retrieval(conversion_results)
    
    # Test error handling
    test_error_handling()
    
    print("\n" + "=" * 50)
    print("🎉 Testing complete!")
    print(f"📊 Frontend available at: {FRONTEND_URL}")
    print(f"🔧 DynamoDB Admin at: {DYNAMODB_ADMIN_URL}")
    print(f"📡 API Endpoint: {CONVERSION_API_URL}")

if __name__ == "__main__":
    main()