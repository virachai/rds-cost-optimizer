# Database Infrastructure Setup Guide (Step-by-Step)

This guide provides a comprehensive, top-to-bottom workflow for setting up the **Hybrid RDS Cost Optimizer**. It covers both the foundational AWS infrastructure and the optimizer logic.

---

## Prerequisites

1.  **AWS Account**: An active AWS account with permissions to manage RDS, VPC, Lambda, and CloudWatch.
2.  **AWS CLI**: Installed and configured on your local machine.
3.  **Basic Knowledge**: Familiarity with AWS VPC and RDS concepts.

---

## Step 0: Foundational Infrastructure

If you already have a VPC and an RDS instance, skip to **Step 1**.

### 0.1 Create a VPC

Ensure you have a VPC with at least two subnets in different availability zones (required for RDS Multi-AZ or even just for the Subnet Group).

### 0.2 Create an RDS Instance

1.  Go to the **RDS Console**.
2.  Choose **Create database**.
3.  Engine: PostgreSQL (recommended) or MySQL.
4.  Connectivity: Ensure it is placed within your VPC.
5.  **Note the DB Instance ID** (e.g., `my-dev-db`).

---

## Step 1: IAM Permissions & Security

We need two primary roles: one for the Lambda functions and one for VPC Flow Logs to write to CloudWatch.

### 1.1 Lambda Execution Role

1.  Create a role named `RDSCostOptimizerLambdaRole` with **Lambda** as the trusted service.
2.  Attach an inline policy using the content from [aws/iam-policy.json](file:///d:/dev/antigravity/rds-cost-optimizer/aws/iam-policy.json).
    - _Self-Correction_: Update the ARNs in this JSON to match your Account ID and RDS Instance ID.

### 1.2 VPC Flow Logs Role

1.  Create a role named `VPCFlowLogToCWLRole` with **VPC Flow Logs** as the trusted service.
2.  Ensure it has permissions to `logs:CreateLogGroup`, `logs:CreateLogStream`, `logs:PutLogEvents`, and `logs:DescribeLogGroups`.

---

## Step 2: Traffic Monitoring (VPC Flow Logs)

This is how we detect incoming traffic to "wake up" the database.

1.  Go to the **VPC Console** > **Your VPCs**.
2.  Select your VPC > **Flow logs** > **Create flow log**.
3.  **Filter**: `ALL`.
4.  **Destination**: `Send to CloudWatch Logs`.
5.  **Log Group**: `/aws/vpc/rds-flow-logs`.
6.  **IAM Role**: Select `VPCFlowLogToCWLRole`.

---

## Step 3: Logic Units (Lambda Functions)

Deploy the two core Python scripts that handle the idle detection and the wake-on-traffic logic.

### 3.1 Deploy `RDSCostOptimizer-IdleStop`

- **Source**: [src/idle_detection.py](file:///d:/dev/antigravity/rds-cost-optimizer/src/idle_detection.py)
- **Runtime**: Python 3.9+
- **Environment Variables**:
  - `RDS_INSTANCE_ID`: Your RDS Instance ID.
  - `IDLE_MINUTES`: `60` (default).
- **Timeout**: 1 minute.

### 3.2 Deploy `RDSCostOptimizer-WakeOnTraffic`

- **Source**: [src/wake_on_traffic.py](file:///d:/dev/antigravity/rds-cost-optimizer/src/wake_on_traffic.py)
- **Runtime**: Python 3.9+
- **Environment Variables**:
  - `RDS_INSTANCE_ID`: Your RDS Instance ID.
- **Timeout**: 1 minute.

---

## Step 4: Automation & Triggers

### 4.1 Hourly Idle Check

1.  In the **RDSCostOptimizer-IdleStop** function, add an **EventBridge (CloudWatch Events)** trigger.
2.  Rule: `cron(0 * * * ? *)` (runs at the start of every hour).

### 4.2 Traffic-Based Wake-up

1.  Create a **Metric Filter** on the log group `/aws/vpc/rds-flow-logs`.
2.  **Filter Pattern**:
    `[version, account, eni, source, dest, srcport, destport="5432", protocol="6", packets, bytes, start, end, action, status]`
3.  Create a **CloudWatch Alarm** from this metric:
    - **Threshold**: >= 1.
    - **Period**: 1 minute.
    - **Action**: Trigger the `RDSCostOptimizer-WakeOnTraffic` Lambda.

---

## Step 5: Validation

1.  **Stop Check**: Wait for the hourly cron or manually trigger `RDSCostOptimizer-IdleStop`. Verify the RDS status changes to `stopping`.
2.  **Start Check**: While the DB is stopped, attempt a connection (e.g., `nc -zv <endpoint> 5432`). Verify the `RDSCostOptimizer-WakeOnTraffic` Lambda is triggered and RDS status changes to `starting`.

---

> [!TIP]
> Use the [scripts/wake-up.sh](file:///d:/dev/antigravity/rds-cost-optimizer/scripts/wake-up.sh) for manual wake-ups if you don't want to wait for the alarm.
