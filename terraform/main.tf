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

# IAM Role for Lambda
resource "aws_iam_role" "rds_scheduler_lambda_role" {
  name = "rds-scheduler-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

# IAM Policy for RDS and Logging
resource "aws_iam_policy" "rds_scheduler_policy" {
  name        = "rds-scheduler-policy"
  description = "Allows Lambda to start/stop RDS instances and write logs."

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "rds:StartDBInstance",
          "rds:StopDBInstance",
          "rds:DescribeDBInstances"
        ]
        Resource = "arn:aws:rds:${var.aws_region}:${data.aws_caller_identity.current.account_id}:db:${var.rds_instance_id}"
      },
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy_attach" {
  role       = aws_iam_role.rds_scheduler_lambda_role.name
  policy_arn = aws_iam_policy.rds_scheduler_policy.arn
}

# Zip Lambda function
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../src/lambda_function.py"
  output_path = "${path.module}/lambda.zip"
}

# Lambda Function
resource "aws_lambda_function" "rds_scheduler" {
  filename         = data.archive_file.lambda_zip.output_path
  function_name    = "rds-auto-scheduler"
  role             = aws_iam_role.rds_scheduler_lambda_role.arn
  handler          = "lambda_function.lambda_handler"
  runtime          = "python3.11"
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256
  timeout          = 30

  environment {
    variables = {
      RDS_INSTANCE_ID    = var.rds_instance_id
      MANUAL_OVERRIDE    = var.manual_override
      SLACK_WEBHOOK_URL  = var.slack_webhook_url
    }
  }
}

# EventBridge Rules
resource "aws_cloudwatch_event_rule" "start_schedule" {
  name                = "rds-start-rule"
  description         = "Triggers Lambda to start RDS"
  schedule_expression = "cron(0 1 * ? * MON-FRI *)" # 09:00 SGT is 01:00 UTC
}

resource "aws_cloudwatch_event_rule" "stop_schedule" {
  name                = "rds-stop-rule"
  description         = "Triggers Lambda to stop RDS"
  schedule_expression = "cron(0 10 * ? * MON-FRI *)" # 18:00 SGT is 10:00 UTC
}

# EventBridge Targets
resource "aws_cloudwatch_event_target" "start_lambda_target" {
  rule      = aws_cloudwatch_event_rule.start_schedule.name
  target_id = "TriggerLambdaStart"
  arn       = aws_lambda_function.rds_scheduler.arn
  input     = jsonencode({ "action" = "START" })
}

resource "aws_cloudwatch_event_target" "stop_lambda_target" {
  rule      = aws_cloudwatch_event_rule.stop_schedule.name
  target_id = "TriggerLambdaStop"
  arn       = aws_lambda_function.rds_scheduler.arn
  input     = jsonencode({ "action" = "STOP" })
}

# Lambda Permissions for EventBridge
resource "aws_lambda_permission" "allow_eventbridge_start" {
  statement_id  = "AllowExecutionFromEventBridgeStart"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.rds_scheduler.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.start_schedule.arn
}

resource "aws_lambda_permission" "allow_eventbridge_stop" {
  statement_id  = "AllowExecutionFromEventBridgeStop"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.rds_scheduler.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.stop_schedule.arn
}

data "aws_caller_identity" "current" {}
