#!/usr/bin/env python3
"""
Setup script for local DynamoDB tables
Run this to create the required tables for local testing
"""

import boto3
import sys
import time
from botocore.exceptions import ClientError

def create_dynamodb_tables():
    """Create the required DynamoDB tables for local testing"""
    
    # Connect to local DynamoDB
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url='http://localhost:8000',
        region_name='us-east-1',
        aws_access_key_id='dummy',
        aws_secret_access_key='dummy'
    )
    
    tables_to_create = [
        {
            'TableName': 'RateCacheTable',
            'KeySchema': [
                {
                    'AttributeName': 'RateSnapshotID',
                    'KeyType': 'HASH'
                }
            ],
            'AttributeDefinitions': [
                {
                    'AttributeName': 'RateSnapshotID',
                    'AttributeType': 'S'
                }
            ],
            'BillingMode': 'PAY_PER_REQUEST'
        },
        {
            'TableName': 'ConversionAuditLogTable',
            'KeySchema': [
                {
                    'AttributeName': 'AuditLogTransactionID',
                    'KeyType': 'HASH'
                }
            ],
            'AttributeDefinitions': [
                {
                    'AttributeName': 'AuditLogTransactionID',
                    'AttributeType': 'S'
                }
            ],
            'BillingMode': 'PAY_PER_REQUEST'
        }
    ]
    
    created_tables = []
    
    for table_config in tables_to_create:
        table_name = table_config['TableName']
        
        try:
            # Check if table already exists
            table = dynamodb.Table(table_name)
            table.meta.client.describe_table(TableName=table_name)
            print(f"✅ Table '{table_name}' already exists")
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # Table doesn't exist, create it
                print(f"🔄 Creating table '{table_name}'...")
                
                table = dynamodb.create_table(**table_config)
                created_tables.append(table)
                print(f"✅ Table '{table_name}' created successfully")
            else:
                print(f"❌ Error checking table '{table_name}': {e}")
                return False
    
    # Wait for tables to be active
    if created_tables:
        print("⏳ Waiting for tables to become active...")
        for table in created_tables:
            table.wait_until_exists()
            print(f"✅ Table '{table.table_name}' is now active")
    
    print("\n🎉 All DynamoDB tables are ready for local testing!")
    return True

def list_tables():
    """List all tables in local DynamoDB"""
    try:
        dynamodb = boto3.client(
            'dynamodb',
            endpoint_url='http://localhost:8000',
            region_name='us-east-1',
            aws_access_key_id='dummy',
            aws_secret_access_key='dummy'
        )
        
        response = dynamodb.list_tables()
        tables = response.get('TableNames', [])
        
        print(f"\n📋 Tables in local DynamoDB ({len(tables)}):")
        for table in tables:
            print(f"  - {table}")
        
        return tables
    except Exception as e:
        print(f"❌ Error listing tables: {e}")
        return []

if __name__ == "__main__":
    print("🚀 Setting up local DynamoDB tables for RateLock...")
    
    # Wait a bit for DynamoDB to be ready
    print("⏳ Waiting for DynamoDB to be ready...")
    time.sleep(3)
    
    if create_dynamodb_tables():
        list_tables()
        print("\n✅ Setup complete! You can now run the RateLock services locally.")
    else:
        print("\n❌ Setup failed. Please check your DynamoDB connection.")
        sys.exit(1)