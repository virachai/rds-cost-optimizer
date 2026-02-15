variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "ap-southeast-1"
}

variable "rds_instance_id" {
  description = "Identifier of the RDS instance"
  type        = string
}

variable "manual_override" {
  description = "Flag to disable automation (set to 'true' to override)"
  type        = string
  default     = "false"
}

variable "slack_webhook_url" {
  description = "Slack webhook URL for notifications (optional)"
  type        = string
  default     = ""
}
