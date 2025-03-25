locals {
  lambda_cost_alerter_forwarder_function_name = "cost_alerter_forwarder"
}

module "cost_alerter_forwarder" {
  source = "github.com/wearetechnative/terraform-aws-lambda.git?ref=5ba61dffd4fd93e7ec4d4883f75acab7d56847bd"

  name              = local.lambda_cost_alerter_forwarder_function_name
  role_arn          = module.lambda_cost_alerter_forwarder_lambda_role.role_arn
  role_arn_provided = true

  handler                   = "lambda_function.lambda_handler"
  source_type               = "local"
  source_directory_location = "${path.module}/lambda_cost_alerter_forwarder"
  source_file_name          = null

  kms_key_arn = var.kms_key_arn
  sqs_dlq_arn = var.sqs_dlq_arn
  memory_size = 128
  timeout     = 300
  runtime     = "python3.9"

  environment_variables = {
    "MONITORING_SQS_QUEUE_URL" : "https://${split(":", var.master_observability_receiver_sqs_arn)[2]}.${split(":", var.master_observability_receiver_sqs_arn)[3]}.amazonaws.com/${split(":", var.master_observability_receiver_sqs_arn)[4]}/${split(":", var.master_observability_receiver_sqs_arn)[5]}"
    "BUDGET_SNS_TOPIC_P1" : module.sns_budget["P1"].sns_arn
    "BUDGET_SNS_TOPIC_P2" : module.sns_budget["P2"].sns_arn
    "BUDGET_SNS_TOPIC_P3" : module.sns_budget["P3"].sns_arn
    "CLIENT_NAME" : "${var.client_name}"
    "NOTIFICATION_ENDPOINT" : var.notification_endpoint
    "IS_MANAGED_SERVICE_CLIENT" : var.is_managed_service_client
  }
}

module "lambda_cost_alerter_forwarder_lambda_role" {
  source = "github.com/wearetechnative/terraform-aws-iam-role.git?ref=9229bbd0280807cbc49f194ff6d2741265dc108a"

  role_name = "lambda_cost_alerter_forwarder_lambda_role"
  role_path = "/cost_alerter/"

  aws_managed_policies = []
  customer_managed_policies = {
    "sqs_observability_receiver" : jsondecode(data.aws_iam_policy_document.sqs_observability_receiver.json)
    "allow_sns_publish" : jsondecode(data.aws_iam_policy_document.allow_sns_publish.json)
  }

  trust_relationship = {
    "lambda" : { "identifier" : "lambda.amazonaws.com", "identifier_type" : "Service", "enforce_mfa" : false, "enforce_userprincipal" : false, "external_id" : null, "prevent_account_confuseddeputy" : false }
  }
}

resource "aws_sns_topic_subscription" "cost_alerter_forwarder_sns_source" {
  for_each = module.sns_budget
  topic_arn = each.value.sns_arn
  protocol  = "lambda"
  endpoint  = module.cost_alerter_forwarder.lambda_function_arn

  redrive_policy = jsonencode({
    deadLetterTargetArn = var.sqs_dlq_arn
  })
}

resource "aws_lambda_permission" "cost_alerter_forwarder_sns_source" {
  for_each = module.sns_budget
  statement_id  = "AllowExecutionFromCostAlerterForwarder${each.key}SNSSource"
  action        = "lambda:InvokeFunction"
  function_name = local.lambda_cost_alerter_forwarder_function_name
  principal     = "sns.amazonaws.com"
  source_arn    = each.value.sns_arn

  depends_on = [
    module.cost_alerter_forwarder
  ]
}

data "aws_iam_policy_document" "sqs_observability_receiver" {
  statement {
    sid = "SQSObservabilityReceiver"

    actions = ["sqs:SendMessage"]

    resources = [var.master_observability_receiver_sqs_arn]
  }
}

data "aws_iam_policy_document" "allow_sns_publish" {
  statement {
    sid = "AllowSNSPublish"

    actions = ["SNS:Publish"]

    resources = ["arn:aws:sns:${data.aws_region.current.name}:${data.aws_caller_identity.current.account_id}:*"]
  }
}
