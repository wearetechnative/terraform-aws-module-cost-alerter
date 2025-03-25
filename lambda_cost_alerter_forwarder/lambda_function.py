import json
import boto3
import os

monitoring_account_sqs_url = os.environ['MONITORING_SQS_QUEUE_URL']
client_name = os.environ['CLIENT_NAME']
sns_p1 = os.environ['BUDGET_SNS_TOPIC_P1']
sns_p2 = os.environ['BUDGET_SNS_TOPIC_P2']
sns_p3 = os.environ['BUDGET_SNS_TOPIC_P3']
is_managed_service_client = os.environ['IS_MANAGED_SERVICE_CLIENT']

"""
AWS Lambda function that forwards budget alerts to an SQS queue.

Environment Variables:
    NOTIFICATION_ENDPOINT: URL of the SQS queue to forward messages to
    IS_MANAGED_SERVICE_CLIENT: If "true", additional details for managed service clients are included

Flow:
    1. Receives SNS notifications about AWS budget alerts
    2. Formats them with additional context and instructions
    3. Forwards them to the specified SQS queue or SNS topic
"""

def setup_clients():

    notification_endpoint = os.environ['NOTIFICATION_ENDPOINT']

    clients = {
        'sts': boto3.client("sts"),
    }

    if notification_endpoint.startswith("https://sqs"):
        # Region name must be set or else it defaults to a different region.
        region = notification_endpoint.split(".")[1]
        
        clients['sqs'] = boto3.client('sqs', region_name=region)
    elif notification_endpoint.startswith("arn:aws:sns"):

        clients['sns'] = boto3.client('sns')
    else:
        print(f"Unrecognized notification endpoint format: {notification_endpoint}")
    
    return clients, notification_endpoint

def create_message_details(account_id, budget_subject, priority, is_managed_service_client=False):
    """
    Create message details dictionary based on account type.
    
    Args:
        account_id: AWS account ID
        budget_subject: Subject line from the budget alert
        is_managed_service: Whether this is a managed service client
        
    Returns:
        Dictionary with appropriate account details
    """

    if isinstance(is_managed_service_client, str):
        is_managed_service_client = is_managed_service_client.lower() == "true"
     
    if is_managed_service_client:
    
        return {
            'account_id': account_id,
            'alias': budget_subject,
            'client_name': "Technative_LandingZone",
            'sla': '8x5',
            'account_name': 'Management',
            'priority': priority
        }
    else:
        return {
            'account_id': account_id,
            'alias': budget_subject,
            'account_name': 'Management'            
        }
    
def format_alert_message(account_id, budget_subject, budget_message, message_details, notification_endpoint):
    """
    Format the alert message with instructions and original content.
    
    Args:
        account_id: AWS account ID
        budget_subject: Original budget alert subject
        budget_message: Original budget alert message
        message_details: Dictionary with account details
        
    Returns:
        For SQS returns a JSON format and for SNS a formatted message dictionary
    """

    if notification_endpoint.startswith("https://sqs"):

        message = {
            'direct_message': True,
            'subject': f"A cost alert was triggered on management account {account_id}.",
            'message': f"""
    ------------
    INSTRUCTIONS: Review the budget on {account_id}.
    If it's usage is within reasonable limits (e.g. research the increase) and it's actual usage then increase the threshold in budget_thresholds.json in the management account Terraform repository.
    ------------

    ORIGINAL SUBJECT: {budget_subject}

    ORIGINAL MESSAGE: {budget_message}
    """,
            **message_details  # This unpacks all key-value pairs from message_details
        }

        # Message must be string to be forwarded or else you will get a type error.
        message_json = json.dumps(message)

        return (message_json)
    elif notification_endpoint.startswith("arn:aws:sns"):
        return {
            'subject': f"A cost alert was triggered on management account {account_id}.",
            'message': f"""
------------
INSTRUCTIONS: Review the budget on {account_id}.
If it's usage is within reasonable limits (e.g. research the increase) and it's actual usage then increase the threshold in budget_thresholds.json in the management account Terraform repository.
------------

ORIGINAL SUBJECT: {budget_subject}

ORIGINAL MESSAGE: {budget_message}
"""
        }

def send_notifications(clients, notification_endpoint, message):

    # Sends sns message to the sqs url.
    if notification_endpoint.startswith("https://sqs"):
        return clients['sqs'].send_message(
                QueueUrl=notification_endpoint,
                MessageBody=message,
            )
    elif notification_endpoint.startswith("arn:aws:sns"):
        return clients['sns'].publish(
                TopicArn=notification_endpoint,
                Message=message['message'],
                Subject=message['subject']

            )
    else:
        raise ValueError(f"Unrecognized notification endpoint format: {notification_endpoint}")            

def lambda_handler(event, context):
    """
    Main Lambda handler function.
    
    Args:
        event: Lambda event object containing SNS records with budget alerts
        context: Lambda context object
        
    Returns:
        Response from SQS send_message operation
    """

    print(event) # for easy debugging
    

    # Setup clients and get environment variables
    clients, notification_endpoint = setup_clients()

    # Get account ID
    management_account_id = clients['sts'].get_caller_identity()["Account"]

    print(notification_endpoint)

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

            message_details = create_message_details(
                management_account_id, 
                budget_subject,
                priority,
                is_managed_service_client
            )

            formatted_message = format_alert_message(
                management_account_id,
                budget_subject,
                budget_message,
                message_details,
                notification_endpoint
            )

            # Sends sns message to the notification endpoint.
            response = send_notifications(clients, notification_endpoint, formatted_message)
    except:


        # Sends sns message to the sqs url.
        if notification_endpoint.startswith("https://sqs"):

            # Sends message to the sqs url to the notification endpoint if the endpoint is sqs.
            response = response = send_notifications(clients, notification_endpoint, json.dumps(event))
            raise
        elif notification_endpoint.startswith("arn:aws:sns"):

            exception_message = {
            'subject': f"There is an error with the Cost Alerter Lambda in the Management Account {management_account_id}.",
            'message': f"{event}"
            }

            # Sends message to the sns topic to the notification endpoint if the endpoint is sns.
            response = send_notifications(clients, notification_endpoint, exception_message)
            raise
