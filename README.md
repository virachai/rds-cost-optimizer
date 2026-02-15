# RDS Cost Optimizer (Idle-Aware Strategy)

A serverless AWS automation system to reduce Amazon RDS `db.t4g.micro` compute costs by stopping instances when no connections are detected.

## Strategy: Hybrid Optimization

- **Auto-Stop (Idle Detection):** A Lambda function checks CloudWatch metrics every hour. If `DatabaseConnections` is 0 for 60 minutes, the instance is stopped.
- **Auto-Start (Wake-on-Traffic):** Automatically starts the database when a connection attempt is detected via VPC Flow Logs and CloudWatch Alarms.
- **Manual Control:** Use `scripts/wake-up.sh` for explicit startup.

## Components

1. **Lambda Function (`src/idle_detection.py`)**: Checks CloudWatch metrics and stops the DB.
2. **Lambda Function (`src/wake_on_traffic.py`)**: Starts the DB upon connection attempts.
3. **IAM Policy (`aws/iam-policy.json`)**: Least-privilege permissions for RDS and CloudWatch.
4. **Setup Runbooks:**
   - [AWS Console Guide](aws/RUNBOOK.md)
   - [AWS CLI Guide](aws/CLI_RUNBOOK.md)
5. **Wake-up Script (`scripts/wake-up.sh`)**: Manual trigger to start the DB.

## EventBridge Cron Expression

To run the check every hour, 24/7:

```text
cron(0 * * * ? *)
```

## Manual Wake-up Command

If you have the AWS CLI configured, run:

```bash
aws rds start-db-instance --db-instance-identifier YOUR_DB_ID --region ap-southeast-1
```

Or use the provided script:

```bash
./scripts/wake-up.sh YOUR_DB_ID
```

## Cost Comparison (Singapore)

| Pattern                     | Monthly Compute (Approx) |
| :-------------------------- | :----------------------- |
| **Always On (24/7)**        | ~$18.00                  |
| **Idle-Aware (~30% usage)** | **~$5.40**               |
| **Savings**                 | **~70%**                 |
