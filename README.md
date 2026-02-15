# RDS Cost Optimizer (rds-auto-start-stop)

A zero-infrastructure AWS automation system to automatically start and stop Amazon RDS `db.t4g.micro` instances in `ap-southeast-1` (Singapore) using **GitHub Actions**.

## Features

- **Zero Infrastructure:** No Lambda or Terraform required. Runs directly from GitHub.
- **Automated Scheduling:** Starts at 09:00 SGT and stops at 18:00 SGT (Mon–Fri).
- **Manual Control:** Trigger start/stop anytime via GitHub Actions `workflow_dispatch`.
- **Cost Efficiency:** Reduces compute costs by ~67%.
- **Secure:** Uses GitHub Secrets to store AWS credentials and Instance IDs.

## Architecture

The system uses a simple, modern approach:

- **GitHub Actions:** Acts as both the scheduler and the execution engine.
- **AWS CLI:** Commands are issued directly to the AWS API.
- **GitHub Secrets:** Securely stores sensitive configuration.

## Cost Estimation (Singapore)

| Instance Type  | Usage Pattern       | Monthly Compute Cost | Savings  |
| :------------- | :------------------ | :------------------- | :------- |
| `db.t4g.micro` | 24/7 (Always On)    | ~$18.00              | -        |
| `db.t4g.micro` | 09:00-18:00 Mon-Fri | ~$5.85               | **~67%** |

_Note: Storage/EBS costs are additional and persist while the instance is stopped._

## Project Structure

```text
├── .github/workflows/  # GitHub Action logic
│   └── rds-scheduler.yml
├── docs/               # RFC and architecture
├── aws/                # SSM Runbooks
├── HOW_TO.md           # Step-by-step guide (Thai)
└── DEPLOYMENT.md       # Step-by-step guide (English)
```

## License

MIT
