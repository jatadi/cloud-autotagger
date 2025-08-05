variable "aws_region" {
  description = "AWS region to deploy resources"
  type        = string
  default     = "eu-central-1"  # Using your current region from AWS CLI config
}

variable "environment" {
  description = "Environment name (e.g., dev, prod)"
  type        = string
  default     = "dev"
}

variable "bucket_name" {
  description = "Name of the S3 bucket for file uploads"
  type        = string
  default     = "autotagger-uploads"  # Will be suffixed with random string
}

variable "lambda_runtime" {
  description = "Runtime for Lambda function"
  type        = string
  default     = "python3.9"
}

variable "lambda_timeout" {
  description = "Timeout for Lambda function (in seconds)"
  type        = number
  default     = 30
}

variable "lambda_memory" {
  description = "Memory allocation for Lambda function (in MB)"
  type        = number
  default     = 128
} 