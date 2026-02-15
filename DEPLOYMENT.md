# Deployment Guide

Follow these steps to deploy the RDS Auto Start-Stop scheduler.

## Prerequisites

1. **AWS CLI** configured with appropriate permissions.
2. **Terraform** (>= 1.0) installed.
3. An existing **RDS instance** (`db.t4g.micro`) in `ap-southeast-1`.

## Deployment Steps

1. **Clone the repository:**

   ```bash
   git clone <repo-url>
   cd rds-cost-optimizer/terraform
   ```

2. **Initialize Terraform:**

   ```bash
   terraform init
   ```

3. **Configure Variables:**
   Create a `terraform.tfvars` file or prepare to provide variables via CLI:

   ```hcl
   rds_instance_id   = "your-db-instance-id"
   slack_webhook_url = "https://hooks.slack.com/services/..." # Optional
   ```

4. **Plan Deployment:**

   ```bash
   terraform plan -var="rds_instance_id=your-db-instance-id"
   ```

5. **Apply Infrastructure:**
   ```bash
   terraform apply -var="rds_instance_id=your-db-instance-id"
   ```

## Post-Deployment Verification

1. **Check CloudWatch Logs:**
   Navigate to the `/aws/lambda/rds-auto-scheduler` log group in the AWS Console.
2. **Manual Test:**
   You can manually trigger the Lambda function with the following test event to verify logic:
   ```json
   { "action": "STOP" }
   ```
3. **EventBridge Rules:**
   Verify that two rules (`rds-start-rule` and `rds-stop-rule`) are enabled and targeting the Lambda function.

## Manual Override

To temporarily disable the automated schedule:

1. Navigate to the Lambda configuration in the AWS Console.
2. Set the environment variable `MANUAL_OVERRIDE` to `true`.
3. Set it back to `false` (default) to resume scheduling.
