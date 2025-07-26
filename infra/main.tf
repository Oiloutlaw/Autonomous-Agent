terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}


resource "aws_s3_bucket" "content_storage" {
  bucket = "${var.project_name}-content-${var.environment}-${random_id.bucket_suffix.hex}"
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}

resource "aws_s3_bucket_versioning" "content_storage" {
  bucket = aws_s3_bucket.content_storage.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "content_storage" {
  bucket = aws_s3_bucket.content_storage.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_cloudwatch_log_group" "agent_logs" {
  name              = "/aws/autonomous-agent/${var.environment}"
  retention_in_days = 30
}

resource "aws_iam_role" "agent_role" {
  name = "${var.project_name}-agent-role-${var.environment}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy" "agent_policy" {
  name = "${var.project_name}-agent-policy-${var.environment}"
  role = aws_iam_role.agent_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ]
        Resource = "${aws_s3_bucket.content_storage.arn}/*"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "${aws_cloudwatch_log_group.agent_logs.arn}:*"
      }
    ]
  })
}

output "content_bucket_name" {
  description = "Name of the S3 bucket for content storage"
  value       = aws_s3_bucket.content_storage.bucket
}

output "log_group_name" {
  description = "CloudWatch log group name"
  value       = aws_cloudwatch_log_group.agent_logs.name
}

output "agent_role_arn" {
  description = "ARN of the IAM role for agent operations"
  value       = aws_iam_role.agent_role.arn
}
