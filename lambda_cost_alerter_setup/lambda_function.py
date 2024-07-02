import boto3
import datetime
import os
import json

organizations_client = boto3.client('organizations')
budget_client = boto3.client('budgets')
sts_client = boto3.client("sts")


# ## change to variable in future, this is for testing only
# try:
#     with open('../budget_thresholds.json') as budget_thresholds_file:
#         budget_thresholds = json.loads(budget_thresholds_file)
# except FileNotFoundError:
#     budget_thresholds = {}

budget_thresholds = os.environ('BUDGET_THRESHOLDS')


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

    print("Creating new budgets.")

    budget_version = "V1" # increment to recreate budgets on next run to apply new settings
    default_amount = "10.0"

    custom_budgets = []

    for budget_threshold in budget_thresholds['Accounts']:
        account_id = budget_threshold["Id"]
        account_name = budget_threshold
        custom_account_budget_name = f"{cost_alert_budget_prefix}_{account_id}_{account_name}_{budget_version}"
        custom_budgets.append(custom_account_budget_name)

    for account in account_list:
        account_id = account["Id"]
        account_name = account["Name"]
        account_budget_name = f"{cost_alert_budget_prefix}_{account_id}_{account_name}_{budget_version}"

        if account_budget_name in budget_list:
            print(f"Up to date cost alert already exists for {account_id}.")
            budget_list.remove(account_budget_name)
        else:
            print(f"No up to date cost alert found for {account_id}. Creating one as {account_budget_name}.")
            if account_budget_name in custom_budgets:
                amount = budget_thresholds['Accounts'][account_name]['Budget']
            else:
                amount = default_amount
            old_budget = None

            old_budget_list = list(filter(lambda x: x.startswith(f"{cost_alert_budget_prefix}_{account_id}_"), budget_list))
            if len(old_budget_list) > 0:
                old_budget = old_budget_list[0]

            if old_budget != None:
                response = budget_client.describe_budget(
                    AccountId=management_account_id,
                    BudgetName=old_budget
                )

                amount = response["Budget"]["BudgetLimit"]["Amount"]

                print(f"Inheriting limit from old budget {old_budget} with value {amount}.")
            else:
                print(f"No old budget found for account {account_id}. Using default threshold {amount}.")

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
                                'Address': os.environ['BUDGET_SNS_TOPIC']
                            },
                        ]
                    },
                ]
            )

            print("Created new alarm.")

    print("Deleting budgets from removed accounts or outdated budgets.")

    for budget in budget_list:
        print(f"Deleting budget {budget}.")

        response = budget_client.delete_budget(
            AccountId=management_account_id,
            BudgetName=budget
        )

    print("Done!")
