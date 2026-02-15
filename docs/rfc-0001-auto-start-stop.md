# RFC 0001: RDS Auto Start-Stop Scheduling

- **Author(s):** Senior Cloud Architect
- **Status:** Proposed
- **Last Updated:** 2026-02-15

---

## Table of Contents

1. [Summary](#summary)
2. [Motivation](#motivation)
3. [Problem Statement](#problem-statement)
4. [Goals](#goals)
5. [Non-Goals](#non-goals)
6. [Proposed Architecture](#proposed-architecture)
7. [Detailed Design](#detailed-design)
8. [Security Considerations](#security-considerations)
9. [Cost Analysis (Singapore)](#cost-analysis-singapore)
10. [Alternatives Considered](#alternatives-considered)
11. [Operational Considerations](#operational-considerations)
12. [Rollout Plan](#rollout-plan)
13. [Risks and Mitigations](#risks-and-mitigations)
14. [Future Improvements](#future-improvements)

---

## 1. Summary

This RFC proposes an automated solution to schedule the starting and stopping of Amazon RDS `db.t4g.micro` instances in the `ap-southeast-1` (Singapore) region. The solution leverages AWS native services—Amazon EventBridge, AWS Lambda, IAM, and CloudWatch—to minimize costs for non-production environments by ensuring databases only run during active development hours.

## 2. Motivation

Dev/Test environments often remain idle outside of business hours (evenings and weekends). For a `db.t4g.micro` instance, running 24/7 incurs unnecessary costs. By automating the instance state, we can significantly reduce the monthly AWS bill without impacting developer productivity, provided the schedule aligns with their working hours.

## 3. Problem Statement

Current RDS instances in our development environments run 24 hours a day, 7 days a week. Given that these instances are typically only needed for ~10 hours a day on weekdays, approximately 70% of the runtime (and associated cost) is wasted.

## 4. Goals

- **Cost Reduction:** Drastically lower AWS RDS compute costs for Dev/Test environments.
- **Automation:** Eliminate the need for manual intervention to start/stop instances.
- **Simplicity:** Use a lightweight, native AWS architecture that is easy to maintain.
- **Developer Convenience:** Ensure the database is predictably available when needed.

## 5. Non-Goals

- Managing Aurora Serverless (which has built-in auto-pause).
- Managing production database instances.
- Granular per-user scheduling (the schedule is global per instance/environment).

## 6. Proposed Architecture

### Architecture Diagram (ASCII)

```text
+-------------------------+          +-----------------------+
|  Amazon EventBridge     | triggers |      AWS Lambda       |
|  (Scheduled Rule)       +--------->|  (Python/Boto3)       |
|  - Start: 08:00 SGT     |          |  - Start/Stop Logic   |
|  - Stop:  20:00 SGT     |          |                       |
+-------------------------+          +-----------+-----------+
                                                 |
                                                 | calls RDS API
                                                 v
+-------------------------+          +-----------------------+
|   CloudWatch Logs       |<---------+      Amazon RDS       |
|   (Monitoring/Audit)    |          |   (db.t4g.micro)      |
+-------------------------+          +-----------------------+
```

### Component Explanation

- **Amazon EventBridge:** Acts as the cron-like scheduler. Two rules will be defined: one for the "Start" event and one for the "Stop" event.
- **AWS Lambda:** A Python-based function that receives the event from EventBridge, identifies the target RDS instance (via tags or environment variables), and executes the `start_db_instance` or `stop_db_instance` API call.
- **IAM Role:** A least-privilege execution role for Lambda, allowing only `rds:StartDBInstance`, `rds:StopDBInstance`, and `rds:DescribeDBInstances` actions on specific resources.
- **CloudWatch Logs:** Captures Lambda execution logs for auditing and troubleshooting failure states.

## 7. Detailed Design

### Scheduling Logic

The default schedule will be:

- **Start:** Monday to Friday, 08:00 SGT (00:00 UTC).
- **Stop:** Monday to Friday, 20:00 SGT (12:00 UTC).
- **Weekends:** Remained stopped.

### Lambda Behavior

The Lambda function will:

1. Parse the input event to determine the action (`START` or `STOP`).
2. Identify the target RDS instance using the `DBInstanceIdentifier`.
3. Check the current status of the instance to avoid redundant API calls.
4. Execute the appropriate Boto3 command (`start_db_instance` or `stop_db_instance`).
5. Log the outcome to CloudWatch.

### IAM Policy Model

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
      "Resource": "arn:aws:rds:ap-southeast-1:ACCOUNT_ID:db:instance-name"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:*"
    }
  ]
}
```

### Failure Handling

- **Retries:** EventBridge will naturally retry event delivery. Lambda concurrency and timeouts will be tuned to prevent multiple overlapping executions.
- **Alerting:** A CloudWatch Alarm will be configured to trigger an SNS notification if the Lambda function fails more than once in a 24-hour window.

## 8. Security Considerations

- **Least Privilege:** Lambda role is restricted to specific RDS actions and resource ARNs.
- **No Public Access:** The automation logic resides within the AWS control plane; no VPC access or public endpoints are required for the Lambda to manage RDS states.
- **Audit Trail:** Every start/stop action is logged in CloudWatch and CloudTrail.

## 9. Cost Analysis (Singapore Region)

### db.t4g.micro Pricing (ap-southeast-1)

- **On-Demand Price:** $0.025 per hour.

| Scenario            | Weekly Hours  | Monthly Cost (Approx) |
| :------------------ | :------------ | :-------------------- |
| **Current (24/7)**  | 168 hours     | ~$18.00               |
| **Proposed (12x5)** | 60 hours      | ~$6.45                |
| **Savings**         | **108 hours** | **~64% Reduction**    |

_Note: Storage costs (EBS) remain constant regardless of the instance state and are not included in this compute-only comparison._

## 10. Alternatives Considered

1. **Aurora Serverless v2:** While it supports auto-scaling, the minimum ACU cost exceeds the baseline cost of a `db.t4g.micro`.
2. **AWS Instance Scheduler:** A robust solution but potentially "overkill" for a single-region, single-instance use case. It requires more complex setup (DynamoDB, multiple Lambda functions).
3. **Manual Management:** Prone to human error, resulting in missed savings or developer downtime.

## 11. Operational Considerations

- **Database Backups:** Automated backups continue during the time the instance is stopped, as per AWS standard behavior.
- **Maintenance Windows:** If a maintenance window falls during "stopped" hours, AWS will start the instance to apply updates, then return it to the previous state.

## 12. Rollout Plan

1. **Phase 1:** Deploy Lambda and IAM Role via Terraform/CloudFormation.
2. **Phase 2:** Configure EventBridge "Stop" rule and verify manual Lambda execution.
3. **Phase 3:** Enable "Start" and "Stop" schedules for a 1-week pilot.
4. **Phase 4:** Review logs and confirm cost savings in AWS Cost Explorer.

## 13. Risks and Mitigations

- **Risk:** Developers working late find the DB stopped.
  - **Mitigation:** Provide a manual "Override" button/script or adjust the EventBridge schedule based on team feedback.
- **Risk:** Lambda fails to start the DB, delaying work.
  - **Mitigation:** CloudWatch Alarms with SNS notifications to the dev alias.

## 14. Future Improvements

- **Tag-based Discovery:** Update Lambda to automatically find all instances with a `Schedule: Dev` tag.
- **Slack Integration:** Send a notification to a Slack channel whenever the DB starts or stops.
- **Web Portal:** A simple Internal UI for developers to manually trigger a start/stop if needed outside the schedule.
