#!/usr/bin/env python3
"""
ConversionEngine Service - Microservice 2
High-speed, customer-facing API service that performs currency conversions
using cached rates and creates immutable audit logs.
"""

import os
import json
import uuid
import logging
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import boto3
from botocore.exceptions import ClientError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Flask app initialization
app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

class ConversionEngineService:
    """
    Service responsible for currency conversion and audit logging
    """
    
    def __init__(self):
        """Initialize the ConversionEngine service with AWS clients"""
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
            
        self.rate_cache_table_name = os.getenv('RATE_CACHE_TABLE', 'RateCacheTable')
        self.audit_log_table_name = os.getenv('AUDIT_LOG_TABLE', 'ConversionAuditLogTable')
        
        # Initialize DynamoDB tables
        try:
            self.rate_cache_table = self.dynamodb.Table(self.rate_cache_table_name)
            self.audit_log_table = self.dynamodb.Table(self.audit_log_table_name)
            logger.info(f"Connected to DynamoDB tables: {self.rate_cache_table_name}, {self.audit_log_table_name}")
            if dynamodb_endpoint:
                logger.info(f"Using local DynamoDB endpoint: {dynamodb_endpoint}")
        except Exception as e:
            logger.error(f"Failed to connect to DynamoDB tables: {e}")
            raise
    
    def get_latest_rate_snapshot(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve the most recent rate snapshot from the cache
        """
        try:
            # Use query with GSI if available, otherwise scan with limit
            response = self.rate_cache_table.scan(
                Limit=50,  # Limit to reduce cost
                ProjectionExpression='RateSnapshotID, BaseCurrency, FetchDate, Rates, FetchTimestamp'
            )
            items = response.get('Items', [])
            
            if not items:
                logger.warning("No rate snapshots found in cache")
                return None
            
            # Sort by snapshot ID to get the latest (snapshots are timestamped)
            latest_snapshot = max(items, key=lambda x: x['RateSnapshotID'])
            
            # Validate the snapshot has required data
            if not latest_snapshot.get('Rates'):
                logger.error("Latest snapshot missing rates data")
                return None
                
            logger.info(f"Retrieved latest snapshot: {latest_snapshot['RateSnapshotID']}")
            return latest_snapshot
            
        except ClientError as e:
            logger.error(f"Failed to retrieve rate snapshot: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving snapshot: {e}")
            return None
    
    def generate_audit_transaction_id(self) -> str:
        """
        Generate a unique audit transaction ID for the conversion
        """
        transaction_id = f"audit-{int(datetime.now(timezone.utc).timestamp())}-{str(uuid.uuid4())[:8]}"
        logger.debug(f"Generated audit transaction ID: {transaction_id}")
        return transaction_id
    
    def calculate_conversion(self, from_currency: str, to_currency: str, 
                           amount: Decimal, rates: Dict[str, float]) -> Tuple[Decimal, str]:
        """
        Calculate currency conversion using EUR as pivot currency
        Returns (converted_amount, calculation_method)
        """
        # Normalize currency codes
        from_currency = from_currency.upper()
        to_currency = to_currency.upper()
        
        # If converting to the same currency
        if from_currency == to_currency:
            return amount, "same_currency"
        
        # Get rates (EUR is always 1.0 in our rates dict)
        from_rate = Decimal(str(rates.get(from_currency, 1.0)))
        to_rate = Decimal(str(rates.get(to_currency, 1.0)))
        
        if from_currency == 'EUR':
            # Converting from EUR to another currency
            converted_amount = amount * to_rate
            calculation_method = "eur_to_target"
        elif to_currency == 'EUR':
            # Converting from another currency to EUR
            converted_amount = amount / from_rate
            calculation_method = "source_to_eur"
        else:
            # Converting between two non-EUR currencies (triangulation via EUR)
            # First convert to EUR, then to target currency
            eur_amount = amount / from_rate
            converted_amount = eur_amount * to_rate
            calculation_method = "triangulation"
        
        # Round to 2 decimal places
        converted_amount = converted_amount.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
        
        logger.debug(f"Conversion: {amount} {from_currency} -> {converted_amount} {to_currency} "
                    f"(method: {calculation_method})")
        
        return converted_amount, calculation_method
    
    def create_audit_log(self, transaction_id: str, from_currency: str, to_currency: str,
                        original_amount: Decimal, converted_amount: Decimal,
                        rate_snapshot_id: str, calculation_method: str,
                        rates_used: Dict[str, float]) -> bool:
        """
        Create an immutable audit log entry for the conversion
        """
        try:
            audit_record = {
                'AuditLogTransactionID': transaction_id,
                'FromCurrency': from_currency.upper(),
                'ToCurrency': to_currency.upper(),
                'OriginalAmount': str(original_amount),
                'ConvertedAmount': str(converted_amount),
                'RateSnapshotID': rate_snapshot_id,
                'ConversionTimestamp': datetime.now(timezone.utc).isoformat(),
                'CalculationMethod': calculation_method,
                'RatesUsed': {
                    from_currency.upper(): rates_used.get(from_currency.upper(), 1.0),
                    to_currency.upper(): rates_used.get(to_currency.upper(), 1.0)
                },
                'ServiceVersion': '1.0.0'
            }
            
            # Store in audit log table
            self.audit_log_table.put_item(Item=audit_record)
            
            logger.info(f"Created audit log entry: {transaction_id}")
            return True
            
        except ClientError as e:
            logger.error(f"Failed to create audit log: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error creating audit log: {e}")
            return False
    
    def perform_conversion(self, from_currency: str, to_currency: str, 
                          amount: str) -> Dict[str, Any]:
        """
        Main conversion method that handles the entire conversion process
        """
        try:
            # Validate and parse amount
            try:
                amount_decimal = Decimal(amount)
                if amount_decimal <= 0:
                    raise ValueError("Amount must be positive")
                if amount_decimal > Decimal('1000000000'):  # 1 billion limit
                    raise ValueError("Amount too large")
            except (ValueError, TypeError, InvalidOperation) as e:
                return {
                    'error': f'Invalid amount: {amount}. Must be a positive number.',
                    'status_code': 400
                }
            
            # Validate currency codes
            if not from_currency or not to_currency:
                return {
                    'error': 'Missing currency codes',
                    'status_code': 400
                }
            
            # Normalize and validate currency format
            from_currency_upper = from_currency.upper().strip()
            to_currency_upper = to_currency.upper().strip()
            
            if len(from_currency_upper) != 3 or len(to_currency_upper) != 3:
                return {
                    'error': 'Currency codes must be 3 characters',
                    'status_code': 400
                }
            
            # Get latest rate snapshot
            rate_snapshot = self.get_latest_rate_snapshot()
            if not rate_snapshot:
                return {
                    'error': 'No exchange rates available',
                    'status_code': 503
                }
            
            rates = rate_snapshot.get('Rates', {})
            rate_snapshot_id = rate_snapshot.get('RateSnapshotID')
            
            # Validate that we have rates for the requested currencies
            from_currency_upper = from_currency.upper()
            to_currency_upper = to_currency.upper()
            
            if from_currency_upper != 'EUR' and from_currency_upper not in rates:
                return {
                    'error': f'Currency not supported: {from_currency_upper}',
                    'status_code': 400
                }
            
            if to_currency_upper != 'EUR' and to_currency_upper not in rates:
                return {
                    'error': f'Currency not supported: {to_currency_upper}',
                    'status_code': 400
                }
            
            # Generate audit transaction ID
            transaction_id = self.generate_audit_transaction_id()
            
            # Perform the conversion
            converted_amount, calculation_method = self.calculate_conversion(
                from_currency, to_currency, amount_decimal, rates
            )
            
            # Create audit log
            audit_success = self.create_audit_log(
                transaction_id, from_currency, to_currency,
                amount_decimal, converted_amount, rate_snapshot_id,
                calculation_method, rates
            )
            
            if not audit_success:
                logger.error("Failed to create audit log - conversion aborted")
                return {
                    'error': 'Audit logging failed',
                    'status_code': 500
                }
            
            # Return successful conversion result
            return {
                'converted_amount': float(converted_amount),
                'rate_snapshot_id': rate_snapshot_id,
                'audit_log_transaction_id': transaction_id,
                'from_currency': from_currency_upper,
                'to_currency': to_currency_upper,
                'original_amount': float(amount_decimal),
                'conversion_timestamp': datetime.now(timezone.utc).isoformat(),
                'status_code': 200
            }
            
        except Exception as e:
            logger.error(f"Conversion failed: {e}")
            return {
                'error': f'Internal server error: {str(e)}',
                'status_code': 500
            }
    
    def get_audit_record(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve an audit record by transaction ID
        """
        try:
            response = self.audit_log_table.get_item(
                Key={'AuditLogTransactionID': transaction_id}
            )
            
            if 'Item' not in response:
                logger.warning(f"Audit record not found: {transaction_id}")
                return None
            
            logger.info(f"Retrieved audit record: {transaction_id}")
            return response['Item']
            
        except ClientError as e:
            logger.error(f"Failed to retrieve audit record: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error retrieving audit record: {e}")
            return None

# Initialize the service
conversion_service = ConversionEngineService()

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'ConversionEngine',
        'timestamp': datetime.now(timezone.utc).isoformat()
    }), 200

@app.route('/v1/convert', methods=['GET'])
def convert_currency():
    """
    Public API endpoint for currency conversion
    Expected parameters: from, to, amount
    """
    try:
        # Get query parameters
        from_currency = request.args.get('from')
        to_currency = request.args.get('to')
        amount = request.args.get('amount')
        
        # Validate required parameters
        if not all([from_currency, to_currency, amount]):
            return jsonify({
                'error': 'Missing required parameters: from, to, amount'
            }), 400
        
        # Perform conversion
        result = conversion_service.perform_conversion(from_currency, to_currency, amount)
        
        status_code = result.pop('status_code', 200)
        
        if status_code == 200:
            logger.info(f"Successful conversion: {amount} {from_currency} -> {to_currency}")
        else:
            logger.warning(f"Conversion failed: {result.get('error')}")
        
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"API error in convert endpoint: {e}")
        return jsonify({
            'error': 'Internal server error'
        }), 500

@app.route('/v1/audit/<transaction_id>', methods=['GET'])
def get_audit_record(transaction_id):
    """
    Internal API endpoint for retrieving audit records
    """
    try:
        if not transaction_id:
            return jsonify({
                'error': 'Transaction ID is required'
            }), 400
        
        # Retrieve audit record
        audit_record = conversion_service.get_audit_record(transaction_id)
        
        if not audit_record:
            return jsonify({
                'error': 'Audit record not found'
            }), 404
        
        logger.info(f"Retrieved audit record for transaction: {transaction_id}")
        return jsonify(audit_record), 200
        
    except Exception as e:
        logger.error(f"API error in audit endpoint: {e}")
        return jsonify({
            'error': 'Internal server error'
        }), 500

@app.route('/v1/rates', methods=['GET'])
def get_current_rates():
    """
    Internal endpoint to get current rate snapshot (for debugging/monitoring)
    """
    try:
        snapshot = conversion_service.get_latest_rate_snapshot()
        
        if not snapshot:
            return jsonify({
                'error': 'No rate snapshot available'
            }), 503
        
        return jsonify({
            'rate_snapshot_id': snapshot.get('RateSnapshotID'),
            'base_currency': snapshot.get('BaseCurrency'),
            'fetch_date': snapshot.get('FetchDate'),
            'rates_count': len(snapshot.get('Rates', {})),
            'fetch_timestamp': snapshot.get('FetchTimestamp')
        }), 200
        
    except Exception as e:
        logger.error(f"API error in rates endpoint: {e}")
        return jsonify({
            'error': 'Internal server error'
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Endpoint not found'
    }), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return jsonify({
        'error': 'Internal server error'
    }), 500

def lambda_handler(event, context):
    """
    AWS Lambda handler for API Gateway integration
    """
    try:
        # Extract HTTP method and path
        http_method = event.get('httpMethod', 'GET')
        path = event.get('path', '/')
        query_params = event.get('queryStringParameters') or {}
        
        if path == '/v1/convert' and http_method == 'GET':
            # Handle conversion request
            from_currency = query_params.get('from')
            to_currency = query_params.get('to')
            amount = query_params.get('amount')
            
            if not all([from_currency, to_currency, amount]):
                return {
                    'statusCode': 400,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Missing required parameters: from, to, amount'})
                }
            
            result = conversion_service.perform_conversion(from_currency, to_currency, amount)
            status_code = result.pop('status_code', 200)
            
            return {
                'statusCode': status_code,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(result)
            }
        
        elif path.startswith('/v1/audit/') and http_method == 'GET':
            # Handle audit record request
            transaction_id = path.split('/')[-1]
            audit_record = conversion_service.get_audit_record(transaction_id)
            
            if not audit_record:
                return {
                    'statusCode': 404,
                    'headers': {'Content-Type': 'application/json'},
                    'body': json.dumps({'error': 'Audit record not found'})
                }
            
            return {
                'statusCode': 200,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps(audit_record)
            }
        
        else:
            return {
                'statusCode': 404,
                'headers': {'Content-Type': 'application/json'},
                'body': json.dumps({'error': 'Endpoint not found'})
            }
    
    except Exception as e:
        logger.error(f"Lambda execution failed: {e}")
        return {
            'statusCode': 500,
            'headers': {'Content-Type': 'application/json'},
            'body': json.dumps({'error': 'Internal server error'})
        }

if __name__ == '__main__':
    # For local development and container deployment
    port = int(os.getenv('PORT', 8080))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"Starting ConversionEngine service on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)