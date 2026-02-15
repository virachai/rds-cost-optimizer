# Deployment Guide (GitHub Actions)

Follow these steps to set up the RDS Auto Start-Stop scheduler using GitHub Actions.

## Prerequisites

1. An existing **RDS instance** (`db.t4g.micro`) in `ap-southeast-1`.
2. An **IAM User** with the following permissions:
   ```json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "rds:StartDBInstance",
           "rds:StopDBInstance",
           "rds:DescribeDBInstances"
         ],
         "Resource": "arn:aws:rds:ap-southeast-1:ACCOUNT_ID:db:YOUR_INSTANCE_ID"
       }
     ]
   }
   ```

## Deployment Steps

### 1. Configure GitHub Secrets

Navigate to your GitHub Repository > **Settings** > **Secrets and variables** > **Actions**. Add the following **Repository secrets**:

| Secret Name             | Description                                              |
| :---------------------- | :------------------------------------------------------- |
| `AWS_ACCESS_KEY_ID`     | Your AWS IAM Access Key ID.                              |
| `AWS_SECRET_ACCESS_KEY` | Your AWS IAM Secret Access Key.                          |
| `RDS_INSTANCE_ID`       | The identifier of your RDS instance (e.g., `my-dev-db`). |

### 2. Verify the Workflow

The workflow is automatically defined in `.github/workflows/rds-scheduler.yml`. Once you push this code to GitHub, it will be active.

## Manual Execution

1. Navigate to the **Actions** tab in your GitHub repository.
2. Select the **RDS Auto Start-Stop** workflow.
3. Click **Run workflow**.
4. Choose the action (`START` or `STOP`) and click **Run workflow**.

## Automated Schedule

The workflow is set to run automatically at:

- **09:00 SGT (01:00 UTC)**: START
- **18:00 SGT (10:00 UTC)**: STOP
- Days: Monday to Friday.
