# AWS CLI Setup Runbook: RDS Cost Optimizer

This runbook provides all the AWS CLI commands required to deploy the **Hybrid RDS Cost Optimizer**.

## Setup Variables

Before running the commands, set these variables in your terminal:

```bash
REGION="ap-southeast-1"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
RDS_INSTANCE_ID="your-rds-instance-id"
RDS_RESOURCE_ID=$(aws rds describe-db-instances --db-instance-identifier $RDS_INSTANCE_ID --query "DBInstances[0].DbiResourceId" --output text)
VPC_ID="your-vpc-id"
```

---

## 1. IAM Role & Policy Setup

```bash
# Create the IAM Role for Lambda
aws iam create-role --role-name RDSCostOptimizerLambdaRole \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Principal": { "Service": "lambda.amazonaws.com" }
        }]
    }'

# Attach the inline policy (content from aws/iam-policy.json)
# Note: Manually edit aws/iam-policy.json with your IDs first
aws iam put-role-policy --role-name RDSCostOptimizerLambdaRole \
    --policy-name RDSCostOptimizerPolicy \
    --policy-document file://aws/iam-policy.json
```

---

## 2. VPC Flow Logs Setup

```bash
# Create Log Group
aws logs create-log-group --log-group-name /aws/vpc/rds-flow-logs

# Create IAM Role for VPC Flow Logs
aws iam create-role --role-name VPCFlowLogToCWLRole \
    --assume-role-policy-document '{
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Effect": "Allow",
            "Principal": { "Service": "vpc-flow-logs.amazonaws.com" }
        }]
    }'

# Create Flow Log
aws ec2 create-flow-logs --resource-type VPC --resource-ids $VPC_ID \
    --traffic-type ALL --log-destination-type cloudwatch-logs \
    --log-group-name /aws/vpc/rds-flow-logs --deliver-logs-permission-arn arn:aws:iam::$ACCOUNT_ID:role/VPCFlowLogToCWLRole
```

---

## 3. Lambda Deployment

```bash
# Package the code
zip -j idle_stop.zip src/idle_detection.py
zip -j wake_traffic.zip src/wake_on_traffic.py

# Create Idle-Stop Function
aws lambda create-function --function-name RDSCostOptimizer-IdleStop \
    --runtime python3.9 --handler idle_detection.lambda_handler \
    --role arn:aws:iam::$ACCOUNT_ID:role/RDSCostOptimizerLambdaRole \
    --zip-file fileb://idle_stop.zip \
    --timeout 60 \
    --environment "Variables={RDS_INSTANCE_ID=$RDS_INSTANCE_ID,IDLE_MINUTES=60}"

# Create Wake-on-Traffic Function
aws lambda create-function --function-name RDSCostOptimizer-WakeOnTraffic \
    --runtime python3.9 --handler wake_on_traffic.lambda_handler \
    --role arn:aws:iam::$ACCOUNT_ID:role/RDSCostOptimizerLambdaRole \
    --zip-file fileb://wake_traffic.zip \
    --timeout 60 \
    --environment "Variables={RDS_INSTANCE_ID=$RDS_INSTANCE_ID}"
```

---

## 4. Scheduling & Alarms

```bash
# Setup Schedule for Auto-Stop
aws events put-rule --name RDSCostOptimizer-HourlyCheck --schedule-expression "cron(0 * * * ? *)"

aws lambda add-permission --function-name RDSCostOptimizer-IdleStop \
    --statement-id EventBridgeInvoke --action lambda:InvokeFunction \
    --principal events.amazonaws.com --source-arn arn:aws:events:$REGION:$ACCOUNT_ID:rule/RDSCostOptimizer-HourlyCheck

aws events put-targets --rule RDSCostOptimizer-HourlyCheck \
    --targets "Id"="1","Arn"="arn:aws:lambda:$REGION:$ACCOUNT_ID:function:RDSCostOptimizer-IdleStop"

# Setup Metric Filter
aws logs put-metric-filter --log-group-name /aws/vpc/rds-flow-logs \
    --filter-name RDSConnectionAttempt \
    --filter-pattern '[version, account, eni, source, dest, srcport, destport="5432", protocol="6", packets, bytes, start, end, action, status]' \
    --metric-transformations metricName=RDSConnectionAttempt,metricNamespace=RDSCostOptimizer,metricValue=1

# Setup Alarm
aws cloudwatch put-metric-alarm --alarm-name RDSCostOptimizer-TrafficDetected \
    --metric-name RDSConnectionAttempt --namespace RDSCostOptimizer \
    --statistic Sum --period 60 --threshold 1 --comparison-operator GreaterThanOrEqualToThreshold \
    --evaluation-periods 1 --alarm-actions arn:aws:lambda:$REGION:$ACCOUNT_ID:function:RDSCostOptimizer-WakeOnTraffic

# Add internal permission for CW Alarm to trigger Lambda
aws lambda add-permission --function-name RDSCostOptimizer-WakeOnTraffic \
    --statement-id CloudWatchAlarmInvoke --action lambda:InvokeFunction \
    --principal lambda.alarms.cloudwatch.amazonaws.com
```
