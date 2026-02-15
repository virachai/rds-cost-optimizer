output "lambda_function_arn" {
  description = "ARN of the Lambda function"
  value       = aws_lambda_function.rds_scheduler.arn
}

output "iam_role_arn" {
  description = "ARN of the IAM role"
  value       = aws_iam_role.rds_scheduler_lambda_role.arn
}

output "start_rule_arn" {
  description = "ARN of the EventBridge start rule"
  value       = aws_cloudwatch_event_rule.start_schedule.arn
}

output "stop_rule_arn" {
  description = "ARN of the EventBridge stop rule"
  value       = aws_cloudwatch_event_rule.stop_schedule.arn
}
