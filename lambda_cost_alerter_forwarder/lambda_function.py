import json
import boto3
import os

monitoring_account_sqs_url = os.environ['MONITORING_SQS_QUEUE_URL']
client_name = os.environ['CLIENT_NAME']
sns_p1 = os.environ['BUDGET_SNS_TOPIC_P1']
sns_p2 = os.environ['BUDGET_SNS_TOPIC_P2']
sns_p3 = os.environ['BUDGET_SNS_TOPIC_P3']

sts_client = boto3.client("sts")

management_account_id = sts_client.get_caller_identity()["Account"]

# Region name must be set or else it defaults to a different region.
sqs_client = boto3.client('sqs', region_name=monitoring_account_sqs_url.split(".")[1])

def lambda_handler(event, context):
    print(event) # for easy debugging
    print(monitoring_account_sqs_url)
    priority = "P3"
    try:
        for record in event["Records"]:
            sns_message = record["Sns"]

            budget_subject = sns_message["Subject"]
            budget_message = sns_message["Message"]
            if sns_message["TopicArn"] == sns_p1:
                priority = "P1"
            elif sns_message["TopicArn"] == sns_p2:
                priority = "P2"
            else:
                priority = "P3"

            sns_message = {
                'direct_message': True,
                'subject': f"A cost alert was triggered on management account {management_account_id}.",
                'message': f"""
------------
INSTRUCTIONS: Review the budget on {management_account_id}.
If it's usage is within reasonable limits (e.g. research the increase) and it's actual usage then increase the threshold in budget_thresholds.json in the management account CodeCommit repo
------------



ORIGINAL SUBJECT: {budget_subject}



ORIGINAL MESSAGE: {budget_message}
""",
                'account_id': management_account_id,
                'alias': budget_subject,
                'client_name': client_name,
                'sla': '8x5',
                'account_name': 'Management',
                'priority': priority
            }

            # Message must be string to be forwarded or else you will get a type error.
            sns_message_json = json.dumps(sns_message)

            # Sends sns message to the sqs url.
            response = sqs_client.send_message(
                QueueUrl=monitoring_account_sqs_url,
                MessageBody=sns_message_json,
            )
    except:
        # Sends message to the sqs url even if its not coming from an sns topic.
        response = sqs_client.send_message(
            QueueUrl=monitoring_account_sqs_url,
            MessageBody=json.dumps(event),
        )

        raise
