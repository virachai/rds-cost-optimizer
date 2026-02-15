# RDS Cost Optimizer (rds-auto-start-stop)

A production-ready AWS automation system to automatically start and stop Amazon RDS `db.t4g.micro` instances in `ap-southeast-1` (Singapore) to optimize costs for Dev/Test environments.

## Features

- **Automated Scheduling:** Starts at 09:00 SGT and stops at 18:00 SGT (Mon–Fri).
- **Cost Efficiency:** Reduces compute costs by ~64%.
- **Manual Override:** Environment variable to temporarily disable automation.
- **Slack Notifications:** Optional real-time alerts on instance state changes.
- **Infrastructure as Code:** Fully managed via Terraform.
- **Least Privilege:** Secure IAM roles restricted to specific RDS resources.

## Architecture

The system uses a serverless architecture:

- **EventBridge Rules:** Trigger the scheduler.
- **AWS Lambda:** Executes start/stop logic via Boto3.
- **IAM:** Ensures secure, minimal permissions.
- **CloudWatch Logs:** Provides full auditability.

## Cost Estimation (Singapore)

| Instance Type  | Usage Pattern       | Monthly Compute Cost | Savings  |
| :------------- | :------------------ | :------------------- | :------- |
| `db.t4g.micro` | 24/7 (Always On)    | ~$18.00              | -        |
| `db.t4g.micro` | 09:00-18:00 Mon-Fri | ~$5.85               | **~67%** |

_Note: Storage/EBS costs are additional and persist while the instance is stopped._

## Project Structure

```text
├── docs/               # RFC and documentation
├── src/                # Lambda source code
│   └── lambda_function.py
├── terraform/          # Infrastructure as Code
│   ├── main.tf
│   ├── variables.tf
│   └── outputs.tf
└── DEPLOYMENT.md       # Step-by-step setup guide
```

## License

MIT
