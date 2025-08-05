# AutoTagger - Serverless Metadata Tagging Pipeline

A serverless AWS solution that automatically processes and tags files uploaded to S3, demonstrating modern cloud architecture patterns.

## Features

- Automatic processing of uploaded files (.json, .csv)
- Metadata extraction and tagging
- DynamoDB storage for search and retrieval
- Serverless architecture using AWS Lambda
- Infrastructure as Code using Terraform
- Automated testing with pytest
- CI/CD pipeline with GitHub Actions

## Architecture

- AWS S3 for file storage
- AWS Lambda for serverless processing
- DynamoDB for metadata storage
- CloudWatch for logging and monitoring
- IAM for security and access control

## Prerequisites

- AWS Account (Free Tier compatible)
- AWS CLI configured
- Terraform installed
- Python 3.x
- Git

## Setup

1. Clone the repository
2. Configure AWS credentials
3. Initialize Terraform:
   ```bash
   cd terraform
   terraform init
   terraform apply
   ```
4. Deploy Lambda function:
   ```bash
   cd ../lambda
   pip install -r requirements.txt
   ```

## Testing

Run the tests using pytest:
```bash
pytest tests/
```

## License

MIT

## Author

[Your Name] 