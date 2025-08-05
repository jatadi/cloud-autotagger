import json
import csv
import os
import boto3
from datetime import datetime, timezone
import logging
from io import StringIO

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def get_s3_client():
    """Get S3 client."""
    return boto3.client('s3', region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'))

def get_dynamodb_table():
    """Get DynamoDB table resource."""
    dynamodb = boto3.resource('dynamodb', region_name=os.environ.get('AWS_DEFAULT_REGION', 'us-east-1'))
    table_name = os.getenv('DYNAMODB_TABLE', 'default-table-name')
    return dynamodb.Table(table_name)

def extract_metadata(bucket, key, content_type):
    """Extract metadata from the file in S3."""
    try:
        s3_client = get_s3_client()
        # Get object metadata from S3
        response = s3_client.head_object(Bucket=bucket, Key=key)
        metadata = {
            'file_id': key,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'size': response['ContentLength'],
            'last_modified': response['LastModified'].isoformat(),
            'content_type': content_type,
            'tags': {}
        }
        
        # Get file content
        obj = s3_client.get_object(Bucket=bucket, Key=key)
        content = obj['Body'].read().decode('utf-8')
        
        # Parse content based on file type
        if key.endswith('.json'):
            try:
                data = json.loads(content)
                # Extract department and region if available
                metadata['tags']['department'] = data.get('department', 'unknown')
                metadata['tags']['region'] = data.get('region', 'unknown')
            except json.JSONDecodeError as e:
                logger.error(f"Error parsing JSON content: {str(e)}")
                metadata['tags']['error'] = 'Invalid JSON format'
                
        elif key.endswith('.csv'):
            try:
                csv_file = StringIO(content)
                csv_reader = csv.DictReader(csv_file)
                # Take first row for tags
                first_row = next(csv_reader, None)
                if first_row:
                    metadata['tags']['department'] = first_row.get('department', 'unknown')
                    metadata['tags']['region'] = first_row.get('region', 'unknown')
            except Exception as e:
                logger.error(f"Error parsing CSV content: {str(e)}")
                metadata['tags']['error'] = 'Invalid CSV format'
        
        return metadata
    except Exception as e:
        logger.error(f"Error processing file {key}: {str(e)}")
        raise

def store_metadata(metadata):
    """Store metadata in DynamoDB."""
    try:
        table = get_dynamodb_table()
        table.put_item(Item=metadata)
        logger.info(f"Stored metadata for file: {metadata['file_id']}")
    except Exception as e:
        logger.error(f"Error storing metadata in DynamoDB: {str(e)}")
        raise

def lambda_handler(event, context):
    """
    Lambda function handler to process S3 events.
    Extracts metadata from uploaded files and stores it in DynamoDB.
    """
    try:
        # Process each record in the S3 event
        for record in event['Records']:
            # Get bucket and file info
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            content_type = record['s3']['object'].get('contentType', 'application/octet-stream')
            
            logger.info(f"Processing file: {key} from bucket: {bucket}")
            
            # Extract metadata and store in DynamoDB
            metadata = extract_metadata(bucket, key, content_type)
            store_metadata(metadata)
            
            logger.info(f"Successfully processed file: {key}")
        
        return {
            'statusCode': 200,
            'body': json.dumps('Successfully processed files')
        }
        
    except Exception as e:
        logger.error(f"Error in lambda_handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error processing files: {str(e)}')
        } 