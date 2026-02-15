#!/bin/bash

# Simple script to "Wake up" the RDS instance
# Usage: ./wake-up.sh [instance-id]

INSTANCE_ID=${1:-$RDS_INSTANCE_ID}

if [ -z "$INSTANCE_ID" ]; then
    echo "Error: RDS_INSTANCE_ID is not set and no argument provided."
    echo "Usage: ./wake-up.sh your-db-id"
    exit 1
fi

echo "🚀 Sending Wake-up call to RDS instance: $INSTANCE_ID..."

aws rds start-db-instance --db-instance-identifier $INSTANCE_ID --region ap-southeast-1

if [ $? -eq 0 ]; then
    echo "✅ Success! The instance is starting. This usually takes 3-5 minutes."
    echo "You can check status with: aws rds describe-db-instances --db-instance-identifier $INSTANCE_ID --query 'DBInstances[0].DBInstanceStatus' --output text"
else
    echo "❌ Failed to start instance. Please check your AWS CLI credentials and Instance ID."
fi
