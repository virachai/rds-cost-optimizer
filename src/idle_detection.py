import boto3
import os
import logging
from datetime import datetime, timedelta

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

def lambda_handler(event, context):
    """
    Lambda function to check DatabaseConnections and stop RDS if idle.
    """
    region = os.environ.get('AWS_REGION', 'ap-southeast-1')
    instance_id = os.environ.get('RDS_INSTANCE_ID')
    idle_minutes = int(os.environ.get('IDLE_MINUTES', '60'))

    if not instance_id:
        logger.error("RDS_INSTANCE_ID environment variable is not set.")
        return {"statusCode": 400, "body": "Missing RDS_INSTANCE_ID"}

    rds = boto3.client('rds', region_name=region)
    cloudwatch = boto3.client('cloudwatch', region_name=region)

    try:
        # 1. Check current state
        res = rds.describe_db_instances(DBInstanceIdentifier=instance_id)
        status = res['DBInstances'][0]['DBInstanceStatus']
        
        if status != 'available':
            logger.info(f"Instance {instance_id} is in {status} state. Skipping idle check.")
            return {"statusCode": 200, "body": f"Instance in {status} state."}

        # 2. Query CloudWatch for DatabaseConnections
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=idle_minutes)
        
        logger.info(f"Checking connections for {instance_id} from {start_time} to {end_time}")
        
        metric_res = cloudwatch.get_metric_data(
            MetricDataQueries=[
                {
                    'Id': 'connections',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/RDS',
                            'MetricName': 'DatabaseConnections',
                            'Dimensions': [
                                {'Name': 'DBInstanceIdentifier', 'Value': instance_id}
                            ]
                        },
                        'Period': 60,
                        'Stat': 'Maximum'
                    }
                }
            ],
            StartTime=start_time,
            EndTime=end_time
        )

        values = metric_res['MetricDataResults'][0].get('Values', [])
        
        # If no data or all data is 0, consider it idle
        is_idle = len(values) == 0 or max(values) == 0
        
        if is_idle:
            logger.info(f"No active connections detected in the last {idle_minutes} minutes. Stopping instance {instance_id}...")
            rds.stop_db_instance(DBInstanceIdentifier=instance_id)
            return {"statusCode": 200, "body": f"Stopping idle instance {instance_id}"}
        else:
            logger.info(f"Active connections ({max(values)}) detected. Keeping instance {instance_id} running.")
            return {"statusCode": 200, "body": f"Active connections detected: {max(values)}"}

    except Exception as e:
        logger.error(f"Error checking idle status: {str(e)}")
        return {"statusCode": 500, "body": str(e)}
