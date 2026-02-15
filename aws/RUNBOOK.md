# AWS Setup Runbook: RDS Cost Optimizer (Step-by-Step)

This guide provides the exact steps to set up the **Hybrid RDS Cost Optimizer** using the AWS Management Console.

---

## Step 1: IAM Role Configuration

- **Naming:** `RDSCostOptimizerLambdaRole`
- **Policy Naming:** `RDSCostOptimizerPolicy`

1. Go to the **IAM Console** > **Roles** > **Create role**.
2. Select **AWS service** and the use case **Lambda**.
3. Skip "Add permissions" for now and click **Next**.
4. Name the role **`RDSCostOptimizerLambdaRole`**.
5. Once created, select the role, click **Add permissions** > **Create inline policy**.
6. Switch to the **JSON** tab and paste the contents of `aws/iam-policy.json`.
7. Save the policy as **`RDSCostOptimizerPolicy`**.

---

## Step 2: VPC Flow Logs Setup

- **Naming (Log Group):** `/aws/vpc/rds-flow-logs`
- **Naming (Role):** `VPCFlowLogToCWLRole`

1. Go to the **VPC Console** > **Your VPCs**.
2. Select the VPC where your RDS is located.
3. Click the **Flow logs** tab > **Create flow log**.
4. Settings:
   - **Filter:** All
   - **Destination:** Send to CloudWatch Logs
   - **Log Group:** `/aws/vpc/rds-flow-logs`
   - **IAM Role:** Ensure the role has permissions to write to CloudWatch.

---

## Step 3: Deployment of Lambda Functions

You will need to create two (2) separate Lambda functions.

### Function A: Auto-Stop

- **Naming:** `RDSCostOptimizer-IdleStop`

1. Go to **Lambda Console** > **Create function**.
2. Name: **`RDSCostOptimizer-IdleStop`**.
3. Runtime: **Python 3.x**.
4. Permissions: Select **Use an existing role** and pick `RDSCostOptimizerLambdaRole`.
5. Paste code from `src/idle_detection.py`.
6. **Environment Variables**:
   - `RDS_INSTANCE_ID`: Your RDS Instance ID.
   - `IDLE_MINUTES`: `60`.
7. **Timeout**: Go to **Configuration** > **General configuration** > Set timeout to **1 minute**.

### Function B: Wake-on-Traffic

- **Naming:** `RDSCostOptimizer-WakeOnTraffic`

1. Go to **Lambda Console** > **Create function**.
2. Name: **`RDSCostOptimizer-WakeOnTraffic`**.
3. Permissions: Select `RDSCostOptimizerLambdaRole`.
4. Paste code from `src/wake_on_traffic.py`.
5. **Environment Variables**:
   - `RDS_INSTANCE_ID`: Your RDS Instance ID.
6. **Timeout**: Set to **1 minute**.

---

## Step 4: Triggers configuration

### Schedule (Auto-Stop)

- **Naming (EventBridge Rule):** `RDSCostOptimizer-HourlyCheck`

1. In the **RDSCostOptimizer-IdleStop** function, click **Add trigger**.
2. Select **EventBridge (CloudWatch Events)**.
3. Name: **`RDSCostOptimizer-HourlyCheck`**.
4. Rule type: **Schedule expression**.
5. Schedule: `cron(0 * * * ? *)`.

### Traffic Alarm (Wake-on-Traffic)

- **Naming (Metric Filter):** `RDSConnectionAttempt`
- **Naming (CloudWatch Alarm):** `RDSCostOptimizer-TrafficDetected`

1. Go to **CloudWatch Console** > **Logs** > **Log Groups** > `/aws/vpc/rds-flow-logs`.
2. Click **Actions** > **Create metric filter**.
3. **Filter pattern**:
   `[version, account, eni, source, dest, srcport, destport="5432", protocol="6", packets, bytes, start, end, action, status]`
   _(Change 5432 to 3306 for MySQL)_.
4. Name the metric `RDSConnectionAttempt`.
5. Click **Create Alarm** from this filter:
   - Name: **`RDSCostOptimizer-TrafficDetected`**.
   - **Threshold**: `Static`, `Greater than or equal to 1`.
   - **Period**: `1 minute`.
6. Set the Alarm action:
   - Send notification to **None** (optional).
   - Go to the **RDSCostOptimizer-WakeOnTraffic** Lambda > **Add trigger** > **CloudWatch Alarm** > Select your new alarm.

---

## Step 5: Verification

1. Check CloudWatch Logs for the `RDS-Idle-Stop` function to see it querying the metrics.
2. Try to connect to your endpoint while the DB is stopped: `nc -zv <endpoint> 5432`.
3. Watch the `RDS-Wake-on-Traffic` logs to see it triggering the database startup.
