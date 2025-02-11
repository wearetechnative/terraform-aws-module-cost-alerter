import boto3
import datetime
import os
import json

organizations_client = boto3.client('organizations')
budget_client = boto3.client('budgets')
sts_client = boto3.client("sts")

budget_thresholds = json.loads(os.environ['BUDGET_THRESHOLDS'])
management_account_id = sts_client.get_caller_identity()["Account"]

def lambda_handler(event, context):
    next_token = None

    print("Listing AWS accounts.")

    account_list = []
    next_token = "x"

    while next_token != None:
        if next_token == "x":
            next_token = None

        args = {
            'MaxResults': 10
        }

        if next_token != None:
              args["NextToken"] = next_token

        response = organizations_client.list_accounts(**args)

        for account in response["Accounts"]:
             account_list.append({ "Id": account["Id"], "Name": account["Name"] })

        if "NextToken" in response:
             next_token = response["NextToken"]
        else:
             next_token = None

    print("Found accounts:")
    print(account_list)

    print("Listing budgets.")

    budget_list = []
    cost_alert_budget_prefix = "cost_alert_budget"
    next_token = "x"

    while next_token != None:
        if next_token == "x":
            next_token = None

        args = {
            'AccountId': management_account_id
            , 'MaxResults': 10
        }

        if next_token != None:
              args["NextToken"] = next_token

        response = budget_client.describe_budgets(**args)

        if "Budgets" in response:
            for budget in response["Budgets"]:
                budget_name = budget["BudgetName"]
                if budget_name.startswith(f"{cost_alert_budget_prefix}_"):
                    budget_list.append(budget_name)

        if "NextToken" in response:
             next_token = response["NextToken"]
        else:
             next_token = None

    print("Found budgets:")
    print(budget_list)

    for budget in budget_list:
        print(f"Deleting budget {budget}.")

        response = budget_client.delete_budget(
            AccountId=management_account_id,
            BudgetName=budget
        )

    print("Creating new budgets.")

    default_amount = "10.0"

    custom_budgets = []

    for account in budget_thresholds['Accounts']:
        account_id = budget_thresholds['Accounts'][account]['Id']
        account_name = account
        custom_account_budget_name = f"{cost_alert_budget_prefix}_{account_id}_{account_name}"
        custom_budgets.append(custom_account_budget_name)
    print("Custom Budgets:")
    print(custom_budgets)

    for account in account_list:
        account_id = account["Id"]
        account_name = account["Name"]
        account_budget_name = f"{cost_alert_budget_prefix}_{account_id}_{account_name}"


        if account_budget_name in custom_budgets:
            amount = budget_thresholds['Accounts'][account_name]['Budget']
        else:
            amount = default_amount
 
        response = budget_client.create_budget(
            AccountId=management_account_id,
            Budget={
                'BudgetName': account_budget_name,
                'BudgetLimit': {
                    'Amount': amount,
                    'Unit': 'USD'
                },
                'CostFilters': {
                    'LinkedAccount': [ account_id ]
                },
                'CostTypes': {
                    'IncludeTax': False,
                    'IncludeSubscription': False,
                    'UseBlended': False,
                    'IncludeRefund': False,
                    'IncludeCredit': False,
                    'IncludeUpfront': False,
                    'IncludeRecurring': False,
                    'IncludeOtherSubscription': False,
                    'IncludeSupport': False,
                    'IncludeDiscount': False,
                    'UseAmortized': False
                },
                'TimeUnit': 'DAILY',
                'TimePeriod': {
                    'Start': "2020-01-01T00:00:00+02:00",
                    'End': "3706473600" # Unable to create/update budget - end time should not be after timestamp 3706473600
                },
                'BudgetType': 'COST'
            },
            NotificationsWithSubscribers=[
                {
                    'Notification': {
                        'NotificationType': 'ACTUAL',
                        'ComparisonOperator': 'GREATER_THAN',
                        'Threshold': 100.0,
                        'ThresholdType': 'PERCENTAGE',
                        'NotificationState': 'ALARM'
                    },
                    'Subscribers': [
                        {
                            'SubscriptionType': 'SNS',
                            'Address': os.environ['BUDGET_SNS_TOPIC_P3']
                        },
                    ]
                },
                {
                    'Notification': {
                        'NotificationType': 'ACTUAL',
                        'ComparisonOperator': 'GREATER_THAN',
                        'Threshold': 200.0,
                        'ThresholdType': 'PERCENTAGE',
                        'NotificationState': 'ALARM'
                    },
                    'Subscribers': [
                        {
                            'SubscriptionType': 'SNS',
                            'Address': os.environ['BUDGET_SNS_TOPIC_P2']
                        },
                    ]
                },
                {
                    'Notification': {
                        'NotificationType': 'ACTUAL',
                        'ComparisonOperator': 'GREATER_THAN',
                        'Threshold': 400.0,
                        'ThresholdType': 'PERCENTAGE',
                        'NotificationState': 'ALARM'
                    },
                    'Subscribers': [
                        {
                            'SubscriptionType': 'SNS',
                            'Address': os.environ['BUDGET_SNS_TOPIC_P1']
                        },
                    ]
                },
            ]
        )
        print("Created new alarm.")

    print("Done!")