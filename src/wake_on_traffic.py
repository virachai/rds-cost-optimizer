import boto3
import os
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda function triggered by CloudWatch Alarm/EventBridge when traffic is detected.
    Starts the RDS instance if it is currently stopped.
    """
    region = os.environ.get('AWS_REGION', 'ap-southeast-1')
    instance_id = os.environ.get('RDS_INSTANCE_ID')

    if not instance_id:
        logger.error("RDS_INSTANCE_ID environment variable is not set.")
        return {"statusCode": 400, "body": "Missing RDS_INSTANCE_ID"}

    rds = boto3.client('rds', region_name=region)

    try:
        # 1. Check current state
        res = rds.describe_db_instances(DBInstanceIdentifier=instance_id)
        status = res['DBInstances'][0]['DBInstanceStatus']
        
        logger.info(f"Traffic detected. Current RDS status: {status}")

        # 2. Start if stopped
        if status == 'stopped':
            logger.info(f"Starting RDS instance {instance_id} due to traffic detection...")
            rds.start_db_instance(DBInstanceIdentifier=instance_id)
            return {"statusCode": 200, "body": f"Starting {instance_id} via Wake-on-Traffic"}
        else:
            logger.info(f"Instance {instance_id} is already {status}. No action taken.")
            return {"statusCode": 200, "body": f"Instance in {status} state."}

    except Exception as e:
        logger.error(f"Error in Wake-on-Traffic: {str(e)}")
        return {"statusCode": 500, "body": str(e)}
