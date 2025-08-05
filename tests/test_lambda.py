import json
import os
import pytest
import boto3
from moto import mock_aws
from datetime import datetime, UTC
import sys
import csv
from io import StringIO
import time

# Add lambda directory to Python path so we can import the lambda function
sys.path.append(os.path.join(os.path.dirname(__file__), '../lambda'))

# Test data
TEST_BUCKET = "test-bucket"
TEST_TABLE = "test-table"
JSON_KEY = "test.json"
CSV_KEY = "test.csv"

# Sample test data
SAMPLE_JSON = {
    "department": "finance",
    "region": "west"
}

SAMPLE_CSV = """department,region
finance,west"""

@pytest.fixture(autouse=True)
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
    os.environ["DYNAMODB_TABLE"] = TEST_TABLE

@pytest.fixture
def aws_services():
    """Set up mocked AWS services."""
    with mock_aws():
        # Create S3 bucket (no location constraint needed for us-east-1)
        s3 = boto3.client("s3")
        s3.create_bucket(Bucket=TEST_BUCKET)
        
        # Create DynamoDB table
        dynamodb = boto3.resource("dynamodb", region_name="us-east-1")
        table = dynamodb.create_table(
            TableName=TEST_TABLE,
            KeySchema=[
                {"AttributeName": "file_id", "KeyType": "HASH"},
                {"AttributeName": "timestamp", "KeyType": "RANGE"}
            ],
            AttributeDefinitions=[
                {"AttributeName": "file_id", "AttributeType": "S"},
                {"AttributeName": "timestamp", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST"
        )
        
        # Wait for table to be active
        waiter = boto3.client('dynamodb', region_name='us-east-1').get_waiter('table_exists')
        waiter.wait(TableName=TEST_TABLE)
        
        yield s3, table

# Import lambda_handler after setting up mocks
from lambda_function import lambda_handler

def create_s3_event(bucket, key):
    """Create a mock S3 event."""
    return {
        "Records": [
            {
                "s3": {
                    "bucket": {"name": bucket},
                    "object": {
                        "key": key,
                        "size": 100,
                        "contentType": "application/json" if key.endswith('.json') else "text/csv"
                    }
                }
            }
        ]
    }

def test_process_json_file(aws_services):
    """Test processing a JSON file."""
    s3, dynamodb = aws_services
    
    # Upload test JSON to S3
    s3.put_object(
        Bucket=TEST_BUCKET,
        Key=JSON_KEY,
        Body=json.dumps(SAMPLE_JSON)
    )
    
    # Create and process S3 event
    event = create_s3_event(TEST_BUCKET, JSON_KEY)
    response = lambda_handler(event, None)
    
    # Assert Lambda response
    assert response["statusCode"] == 200
    
    # Check DynamoDB entry
    items = dynamodb.scan()["Items"]
    assert len(items) == 1
    item = items[0]
    
    assert item["file_id"] == JSON_KEY
    assert item["tags"]["department"] == "finance"
    assert item["tags"]["region"] == "west"

def test_process_csv_file(aws_services):
    """Test processing a CSV file."""
    s3, dynamodb = aws_services
    
    # Upload test CSV to S3
    s3.put_object(
        Bucket=TEST_BUCKET,
        Key=CSV_KEY,
        Body=SAMPLE_CSV
    )
    
    # Create and process S3 event
    event = create_s3_event(TEST_BUCKET, CSV_KEY)
    response = lambda_handler(event, None)
    
    # Assert Lambda response
    assert response["statusCode"] == 200
    
    # Check DynamoDB entry
    items = dynamodb.scan()["Items"]
    assert len(items) == 1
    item = items[0]
    
    assert item["file_id"] == CSV_KEY
    assert item["tags"]["department"] == "finance"
    assert item["tags"]["region"] == "west"

def test_invalid_json(aws_services):
    """Test handling invalid JSON file."""
    s3, dynamodb = aws_services
    
    # Upload invalid JSON to S3
    s3.put_object(
        Bucket=TEST_BUCKET,
        Key=JSON_KEY,
        Body="invalid json content"
    )
    
    # Create and process S3 event
    event = create_s3_event(TEST_BUCKET, JSON_KEY)
    response = lambda_handler(event, None)
    
    # Assert Lambda response
    assert response["statusCode"] == 200  # Still succeeds but with error tag
    
    # Check DynamoDB entry
    items = dynamodb.scan()["Items"]
    assert len(items) == 1
    item = items[0]
    
    assert item["file_id"] == JSON_KEY
    assert "error" in item["tags"]
    assert item["tags"]["error"] == "Invalid JSON format"

def test_invalid_csv(aws_services):
    """Test handling invalid CSV file."""
    s3, dynamodb = aws_services
    
    # Upload invalid CSV to S3
    s3.put_object(
        Bucket=TEST_BUCKET,
        Key=CSV_KEY,
        Body="invalid,csv\nno header row"
    )
    
    # Create and process S3 event
    event = create_s3_event(TEST_BUCKET, CSV_KEY)
    response = lambda_handler(event, None)
    
    # Assert Lambda response
    assert response["statusCode"] == 200  # Still succeeds but with unknown tags
    
    # Check DynamoDB entry
    items = dynamodb.scan()["Items"]
    assert len(items) == 1
    item = items[0]
    
    assert item["file_id"] == CSV_KEY
    assert item["tags"]["department"] == "unknown"  # Default value for missing field 