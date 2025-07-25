output "infrastructure_summary" {
  description = "Summary of deployed infrastructure"
  value = {
    content_bucket    = aws_s3_bucket.content_storage.bucket
    log_group        = aws_cloudwatch_log_group.agent_logs.name
    agent_role_arn   = aws_iam_role.agent_role.arn
    region           = var.aws_region
    environment      = var.environment
  }
}

output "deployment_commands" {
  description = "Commands to configure the application with infrastructure"
  value = {
    aws_bucket_env = "export AWS_S3_BUCKET=${aws_s3_bucket.content_storage.bucket}"
    aws_region_env = "export AWS_REGION=${var.aws_region}"
    log_group_env  = "export AWS_LOG_GROUP=${aws_cloudwatch_log_group.agent_logs.name}"
  }
}
