import json
import os

from lambda_function import *

class CognitoIdentity():
    cognito_identity_id='None'
    cognito_identity_pool_id='None'

class LambdaContext():
    aws_request_id='f3090957-185e-4719-a144-83f813f05bba'
    log_group_name='/aws/lambda/saleforce_archiver_lambda'
    log_stream_name='2022/10/10/[$LATEST]6b4976d7c5f54d7d8186dddc7dec210a'
    function_name='saleforce_archiver_lambda'
    memory_limit_in_mb=128
    function_version='$LATEST'
    invoked_function_arn='arn:aws:lambda:eu-central-1:228305040478:function:saleforce_archiver_lambda'
    client_context='None'
    identity=CognitoIdentity()

f = open("lambda_test_event.json", "r")
event = json.loads(f.read()) # can be any event since this Lambda is triggered by EventBridge
f.close()

os.environ['BUDGET_SNS_TOPIC'] = "arn:aws:sns:eu-central-1:617813585939:sns_budget-20230328094531880000000002"

lambda_handler(event, LambdaContext())
