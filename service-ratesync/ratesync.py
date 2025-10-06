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
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from decimal import Decimal
import boto3
import httpx
from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic Models for FastAPI
class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str
    last_sync: Optional[str] = None

class SyncResponse(BaseModel):
    status: str
    snapshot_id: str
    currencies_updated: int
    timestamp: str

class RateSyncService:
    """
    Service responsible for fetching exchange rates and storing them in DynamoDB
    """
    
    def __init__(self):
        """Initialize the RateSync service with AWS clients"""
        # Configure DynamoDB endpoint for local testing
        dynamodb_endpoint = os.getenv('DYNAMODB_ENDPOINT')
        if dynamodb_endpoint:
            self.dynamodb = boto3.resource(
                'dynamodb',
                endpoint_url=dynamodb_endpoint,
                region_name=os.getenv('AWS_DEFAULT_REGION', 'us-east-1'),
                aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID', 'dummy'),
                aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY', 'dummy')
            )
        else:
            self.dynamodb = boto3.resource('dynamodb')
            
        self.table_name = os.getenv('RATE_CACHE_TABLE', 'RateCacheTable')
        self.frankfurter_api_url = 'https://api.frankfurter.app/latest'
        
        # Initialize DynamoDB table
        try:
            self.rate_cache_table = self.dynamodb.Table(self.table_name)
            logger.info(f"Connected to DynamoDB table: {self.table_name}")
            if dynamodb_endpoint:
                logger.info(f"Using local DynamoDB endpoint: {dynamodb_endpoint}")
        except Exception as e:
            logger.error(f"Failed to connect to DynamoDB table: {e}")
            raise
    
    def generate_snapshot_id(self) -> str:
        """
        Generate a unique Rate Snapshot ID based on current timestamp
        Format: YYYYMMDD-HHMMUTC with microseconds for uniqueness
        """
        now = datetime.now(timezone.utc)
        # Add microseconds to prevent collisions in rapid testing
        snapshot_id = now.strftime("%Y%m%d-%H%M%fUTC")
        logger.info(f"Generated snapshot ID: {snapshot_id}")
        return snapshot_id
    
    def check_existing_snapshot(self, snapshot_id: str) -> bool:
        """
        Check if a snapshot with the given ID already exists
        """
        try:
            response = self.rate_cache_table.get_item(
                Key={'RateSnapshotID': snapshot_id}
            )
            exists = 'Item' in response
            if exists:
                logger.info(f"Snapshot {snapshot_id} already exists, skipping...")
            return exists
        except Exception as e:
            logger.error(f"Error checking existing snapshot: {e}")
            return False
    
    async def fetch_rates_from_frankfurter(self, max_retries: int = 3) -> Optional[Dict[str, Any]]:
        """
        Fetch the latest exchange rates from Frankfurter API with retry logic
        Returns rates with EUR as base currency
        """
        for attempt in range(max_retries):
            try:
                logger.info(f"Fetching rates from Frankfurter API (attempt {attempt + 1}/{max_retries})...")
                
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(self.frankfurter_api_url)
                    response.raise_for_status()
                    
                    data = response.json()
                    logger.info(f"Successfully fetched rates for {len(data.get('rates', {}))} currencies")
                    return data
                
            except httpx.TimeoutException:
                logger.warning(f"Attempt {attempt + 1} timed out")
            except httpx.HTTPError as e:
                logger.warning(f"Attempt {attempt + 1} failed: {e}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON response from Frankfurter API: {e}")
                break  # Don't retry on JSON decode errors
            except Exception as e:
                logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt  # Exponential backoff
                logger.info(f"Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                logger.error(f"All {max_retries} attempts failed to fetch rates from Frankfurter API")
        
        return None
    
    def store_rates_in_cache(self, snapshot_id: str, rates_data: Dict[str, Any]) -> bool:
        """
        Store the fetched rates in DynamoDB with the snapshot ID
        """
        try:
            # Calculate TTL (30 days from now)
            ttl_timestamp = int(time.time()) + (30 * 24 * 60 * 60)
            
            # Convert float rates to Decimal for DynamoDB compatibility
            decimal_rates = {}
            for currency, rate in rates_data.get('rates', {}).items():
                decimal_rates[currency] = Decimal(str(rate))
            
            # Add EUR to rates with value 1.0 (since it's the base currency)
            decimal_rates['EUR'] = Decimal('1.0')
            
            # Prepare the item for DynamoDB
            cache_item = {
                'RateSnapshotID': snapshot_id,
                'BaseCurrency': rates_data.get('base', 'EUR'),
                'FetchDate': rates_data.get('date'),
                'Rates': decimal_rates,
                'FetchTimestamp': datetime.now(timezone.utc).isoformat(),
                'TTL': ttl_timestamp
            }
            
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
    
    async def sync_rates(self) -> bool:
        """
        Main method to sync rates - fetch from API and store in cache
        """
        logger.info("Starting rate synchronization process...")
        
        # Generate snapshot ID
        snapshot_id = self.generate_snapshot_id()
        
        # Check if this snapshot already exists (prevent duplicates)
        if self.check_existing_snapshot(snapshot_id):
            logger.info("Snapshot already exists, synchronization not needed")
            return True
        
        # Fetch rates from Frankfurter API with retry logic
        rates_data = await self.fetch_rates_from_frankfurter()
        if not rates_data:
            logger.error("Failed to fetch rates from API after all retries")
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

# Initialize the service
rate_sync_service = RateSyncService()

# Create FastAPI app
app = FastAPI(
    title="RateLock RateSync",
    description="Asynchronous worker for fetching and caching exchange rates",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint for load balancer"""
    # Get the latest snapshot to check service status
    try:
        latest = rate_sync_service.get_latest_snapshot()
        last_sync = latest.get('CollectionTimestamp') if latest else None
    except Exception:
        last_sync = None
    
    return HealthResponse(
        status="healthy",
        service="RateSync",
        timestamp=datetime.now(timezone.utc).isoformat(),
        last_sync=last_sync
    )

@app.post("/sync", response_model=SyncResponse)
async def trigger_sync():
    """
    Manually trigger rate synchronization
    Typically called by AWS EventBridge on schedule
    """
    try:
        logger.info("Manual sync triggered via API")
        
        # Generate snapshot ID for this sync
        snapshot_id = rate_sync_service.generate_snapshot_id()
        
        # Perform the sync
        success = await rate_sync_service.sync_rates()
        
        if success:
            # Get the latest snapshot to return details
            latest = rate_sync_service.get_latest_snapshot()
            if latest and latest.get('RateSnapshotID') == snapshot_id:
                return SyncResponse(
                    status="success",
                    snapshot_id=snapshot_id,
                    currencies_updated=len(latest.get('Rates', {})),
                    timestamp=latest.get('CollectionTimestamp', datetime.now(timezone.utc).isoformat())
                )
            else:
                # Fallback if we can't get the exact snapshot
                return SyncResponse(
                    status="success",
                    snapshot_id=snapshot_id,
                    currencies_updated=0,
                    timestamp=datetime.now(timezone.utc).isoformat()
                )
        else:
            raise HTTPException(
                status_code=500,
                detail="Rate synchronization failed"
            )
            
    except Exception as e:
        logger.error(f"Sync endpoint error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Sync failed: {str(e)}"
        )

# Background task for periodic sync (for container mode)
async def periodic_sync():
    """Background task to sync rates every hour"""
    while True:
        try:
            # Wait 1 hour (3600 seconds)
            await asyncio.sleep(3600)
            
            logger.info("Starting scheduled rate synchronization")
            success = await rate_sync_service.sync_rates()
            
            if success:
                logger.info("Scheduled sync completed successfully")
            else:
                logger.error("Scheduled sync failed")
                
        except Exception as e:
            logger.error(f"Periodic sync error: {e}")

@app.on_event("startup")
async def startup_event():
    """Perform initial rate sync on startup with retry logic and start background tasks"""
    logger.info("RateSync service starting up")
    
    # Start background tasks if in container mode
    if os.getenv('RUN_MODE') == 'container':
        logger.info("Starting periodic rate synchronization (every 1 hour)")
        asyncio.create_task(periodic_sync())
    
    # Perform initial sync with retry logic
    logger.info("Starting initial rate synchronization process...")
    
    max_retries = 10
    retry_delay = 30  # 30 seconds between retries
    
    for attempt in range(1, max_retries + 1):
        try:
            logger.info(f"Initial sync attempt {attempt}/{max_retries}")
            success = await rate_sync_service.sync_rates()
            
            if success:
                logger.info("Initial rate sync completed successfully")
                return  # Exit successfully
            else:
                logger.warning(f"Initial sync attempt {attempt} returned failure")
                if attempt == max_retries:
                    logger.error("All initial sync attempts failed - service will rely on manual sync or periodic schedule")
                    return  # Exit after max retries
                else:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
            
        except Exception as e:
            logger.warning(f"Initial sync attempt {attempt} failed with exception: {e}")
            
            if attempt == max_retries:
                logger.error("All initial sync attempts failed - service will rely on manual sync or periodic schedule")
                return  # Exit after max retries
            else:
                logger.info(f"Retrying in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)

def main():
    """
    Main function for local testing and Docker container execution
    """
    logger.info("RateSync Service starting...")
    
    try:
        # For local testing, run the sync once
        if os.getenv('RUN_MODE') != 'container' and os.getenv('RUN_MODE') != 'server':
            logger.info("Running in test mode - single execution")
            import asyncio
            
            async def test_sync():
                success = await rate_sync_service.sync_rates()
                if success:
                    logger.info("Rate synchronization completed successfully")
                    # Optionally display the latest snapshot for verification
                    latest = rate_sync_service.get_latest_snapshot()
                    if latest:
                        logger.info(f"Latest snapshot contains {len(latest.get('Rates', {}))} currencies")
                else:
                    logger.error("Rate synchronization failed")
                    exit(1)
            
            asyncio.run(test_sync())
        else:
            # Run as FastAPI server
            import uvicorn
            port = int(os.getenv('PORT', 8081))
            logger.info(f"Starting RateSync service on port {port}")
            uvicorn.run(app, host="0.0.0.0", port=port)
    
    except Exception as e:
        logger.error(f"Service execution failed: {e}")
        exit(1)

if __name__ == "__main__":
    main()