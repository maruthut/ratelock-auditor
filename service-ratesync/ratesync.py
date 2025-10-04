#!/usr/bin/env python3
"""
RateSync Service - Microservice 1
Asynchronous worker that fetches exchange rates from Frankfurter API
and stores them in DynamoDB with unique snapshot IDs.
"""

import os
import json
import time
import logging
import requests
import boto3
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RateSyncService:
    """
    Service responsible for fetching exchange rates and storing them in DynamoDB
    """
    
    def __init__(self):
        """Initialize the RateSync service with AWS clients"""
        self.dynamodb = boto3.resource('dynamodb')
        self.table_name = os.getenv('RATE_CACHE_TABLE', 'RateCacheTable')
        self.frankfurter_api_url = 'https://api.frankfurter.app/latest'
        
        # Initialize DynamoDB table
        try:
            self.rate_cache_table = self.dynamodb.Table(self.table_name)
            logger.info(f"Connected to DynamoDB table: {self.table_name}")
        except Exception as e:
            logger.error(f"Failed to connect to DynamoDB table: {e}")
            raise
    
    def generate_snapshot_id(self) -> str:
        """
        Generate a unique Rate Snapshot ID based on current timestamp
        Format: YYYYMMDD-HHMMUTC
        """
        now = datetime.now(timezone.utc)
        snapshot_id = now.strftime("%Y%m%d-%H%MUTC")
        logger.info(f"Generated snapshot ID: {snapshot_id}")
        return snapshot_id
    
    def fetch_rates_from_frankfurter(self) -> Optional[Dict[str, Any]]:
        """
        Fetch the latest exchange rates from Frankfurter API
        Returns rates with EUR as base currency
        """
        try:
            logger.info("Fetching rates from Frankfurter API...")
            response = requests.get(self.frankfurter_api_url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.info(f"Successfully fetched rates for {len(data.get('rates', {}))} currencies")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch rates from Frankfurter API: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response from Frankfurter API: {e}")
            return None
    
    def store_rates_in_cache(self, snapshot_id: str, rates_data: Dict[str, Any]) -> bool:
        """
        Store the fetched rates in DynamoDB with the snapshot ID
        """
        try:
            # Calculate TTL (30 days from now)
            ttl_timestamp = int(time.time()) + (30 * 24 * 60 * 60)
            
            # Prepare the item for DynamoDB
            cache_item = {
                'RateSnapshotID': snapshot_id,
                'BaseCurrency': rates_data.get('base', 'EUR'),
                'FetchDate': rates_data.get('date'),
                'Rates': rates_data.get('rates', {}),
                'FetchTimestamp': datetime.now(timezone.utc).isoformat(),
                'TTL': ttl_timestamp
            }
            
            # Add EUR to rates with value 1.0 (since it's the base currency)
            cache_item['Rates']['EUR'] = 1.0
            
            # Store in DynamoDB
            self.rate_cache_table.put_item(Item=cache_item)
            
            logger.info(f"Successfully stored rates in cache with snapshot ID: {snapshot_id}")
            logger.info(f"Stored {len(cache_item['Rates'])} currency rates")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to store rates in DynamoDB: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error storing rates: {e}")
            return False
    
    def validate_rates_data(self, rates_data: Dict[str, Any]) -> bool:
        """
        Validate the rates data received from Frankfurter API
        """
        if not rates_data:
            logger.error("Rates data is empty or None")
            return False
        
        if 'rates' not in rates_data:
            logger.error("No 'rates' field in response data")
            return False
        
        if not isinstance(rates_data['rates'], dict):
            logger.error("Rates field is not a dictionary")
            return False
        
        if len(rates_data['rates']) == 0:
            logger.error("Rates dictionary is empty")
            return False
        
        # Check if all rate values are numeric
        for currency, rate in rates_data['rates'].items():
            if not isinstance(rate, (int, float)):
                logger.error(f"Invalid rate value for {currency}: {rate}")
                return False
        
        logger.info("Rates data validation passed")
        return True
    
    def sync_rates(self) -> bool:
        """
        Main method to sync rates - fetch from API and store in cache
        """
        logger.info("Starting rate synchronization process...")
        
        # Generate snapshot ID
        snapshot_id = self.generate_snapshot_id()
        
        # Fetch rates from Frankfurter API
        rates_data = self.fetch_rates_from_frankfurter()
        if not rates_data:
            logger.error("Failed to fetch rates from API")
            return False
        
        # Validate rates data
        if not self.validate_rates_data(rates_data):
            logger.error("Rates data validation failed")
            return False
        
        # Store rates in cache
        if not self.store_rates_in_cache(snapshot_id, rates_data):
            logger.error("Failed to store rates in cache")
            return False
        
        logger.info(f"Rate synchronization completed successfully for snapshot: {snapshot_id}")
        return True
    
    def get_latest_snapshot(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve the latest rate snapshot from the cache (for testing/debugging)
        """
        try:
            # Scan table and get the most recent snapshot
            response = self.rate_cache_table.scan()
            items = response.get('Items', [])
            
            if not items:
                logger.warning("No rate snapshots found in cache")
                return None
            
            # Sort by snapshot ID (which includes timestamp) to get the latest
            latest_item = max(items, key=lambda x: x['RateSnapshotID'])
            logger.info(f"Latest snapshot: {latest_item['RateSnapshotID']}")
            return latest_item
            
        except Exception as e:
            logger.error(f"Failed to retrieve latest snapshot: {e}")
            return None

def lambda_handler(event, context):
    """
    AWS Lambda handler for scheduled execution
    This function will be called by EventBridge on a schedule
    """
    logger.info("Lambda function started - Rate sync triggered")
    
    try:
        # Initialize the service
        rate_sync = RateSyncService()
        
        # Perform rate synchronization
        success = rate_sync.sync_rates()
        
        if success:
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Rate synchronization completed successfully',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            }
        else:
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'message': 'Rate synchronization failed',
                    'timestamp': datetime.now(timezone.utc).isoformat()
                })
            }
    
    except Exception as e:
        logger.error(f"Lambda execution failed: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f'Lambda execution error: {str(e)}',
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }

def main():
    """
    Main function for local testing and Docker container execution
    """
    logger.info("RateSync Service starting...")
    
    try:
        # Initialize the service
        rate_sync = RateSyncService()
        
        # For container deployment, run in a loop (simulating scheduled execution)
        if os.getenv('RUN_MODE') == 'container':
            logger.info("Running in container mode - will sync rates every hour")
            while True:
                try:
                    success = rate_sync.sync_rates()
                    if success:
                        logger.info("Rate sync completed successfully, sleeping for 1 hour...")
                    else:
                        logger.error("Rate sync failed, will retry in 1 hour...")
                    
                    # Sleep for 1 hour (3600 seconds)
                    time.sleep(3600)
                    
                except KeyboardInterrupt:
                    logger.info("Received interrupt signal, shutting down...")
                    break
                except Exception as e:
                    logger.error(f"Error in sync loop: {e}")
                    logger.info("Retrying in 1 hour...")
                    time.sleep(3600)
        else:
            # One-time execution for testing
            logger.info("Running in test mode - single execution")
            success = rate_sync.sync_rates()
            
            if success:
                logger.info("Rate synchronization completed successfully")
                
                # Optionally display the latest snapshot for verification
                latest = rate_sync.get_latest_snapshot()
                if latest:
                    logger.info(f"Latest snapshot contains {len(latest.get('Rates', {}))} currencies")
            else:
                logger.error("Rate synchronization failed")
                exit(1)
    
    except Exception as e:
        logger.error(f"Service execution failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()