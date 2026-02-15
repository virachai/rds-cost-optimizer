import boto3
import os
import logging
import json
import urllib3

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

http = urllib3.PoolManager()

def send_slack_notification(message, webhook_url):
    """Sends a notification to a Slack channel."""
    if not webhook_url:
        return
    
    payload = {"text": message}
    try:
        response = http.request(
            'POST',
            webhook_url,
            body=json.dumps(payload),
            headers={'Content-Type': 'application/json'}
        )
        if response.status != 200:
            logger.error(f"Error sending Slack notification: {response.status}, {response.data}")
    except Exception as e:
        logger.error(f"Failed to send Slack notification: {str(e)}")

def lambda_handler(event, context):
    """
    Lambda function to start or stop an Amazon RDS instance.
    Expected event format: {"action": "START" | "STOP"}
    """
    region = os.environ.get('AWS_REGION', 'ap-southeast-1')
    instance_id = os.environ.get('RDS_INSTANCE_ID')
    override_flag = os.environ.get('MANUAL_OVERRIDE', 'false').lower()
    slack_webhook_url = os.environ.get('SLACK_WEBHOOK_URL')

    if not instance_id:
        logger.error("RDS_INSTANCE_ID environment variable is not set.")
        return {"statusCode": 400, "body": "Missing RDS_INSTANCE_ID"}

    if override_flag == 'true':
        logger.info(f"Manual override is active. Skipping scheduled action for {instance_id}.")
        return {"statusCode": 200, "body": "Manual override active. No action taken."}

    action = event.get('action', '').upper()
    rds = boto3.client('rds', region_name=region)

    try:
        # Check current state
        response = rds.describe_db_instances(DBInstanceIdentifier=instance_id)
        status = response['DBInstances'][0]['DBInstanceStatus']
        logger.info(f"Instance {instance_id} current status: {status}")

        if action == 'START':
            if status == 'stopped':
                logger.info(f"Starting RDS instance: {instance_id}")
                rds.start_db_instance(DBInstanceIdentifier=instance_id)
                msg = f"✅ RDS Instance `{instance_id}` is starting as per schedule."
                send_slack_notification(msg, slack_webhook_url)
                return {"statusCode": 200, "body": f"Starting {instance_id}"}
            else:
                logger.info(f"Instance {instance_id} is in {status} state. No start action needed.")
                return {"statusCode": 200, "body": f"Instance in {status} state. No action taken."}

        elif action == 'STOP':
            if status == 'available':
                logger.info(f"Stopping RDS instance: {instance_id}")
                rds.stop_db_instance(DBInstanceIdentifier=instance_id)
                msg = f"🛑 RDS Instance `{instance_id}` is stopping as per schedule."
                send_slack_notification(msg, slack_webhook_url)
                return {"statusCode": 200, "body": f"Stopping {instance_id}"}
            else:
                logger.info(f"Instance {instance_id} is in {status} state. No stop action needed.")
                return {"statusCode": 200, "body": f"Instance in {status} state. No action taken."}

        else:
            logger.error(f"Invalid action provided: {action}")
            return {"statusCode": 400, "body": f"Invalid action: {action}"}

    except Exception as e:
        error_msg = f"❌ Error performing {action} on {instance_id}: {str(e)}"
        logger.error(error_msg)
        send_slack_notification(error_msg, slack_webhook_url)
        return {"statusCode": 500, "body": str(e)}
