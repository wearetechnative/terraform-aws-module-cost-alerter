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
    "SNS_P1" : "${module.sns_budget_p1.sns_arn}"
    "SNS_P2" : "${module.sns_budget_p2.sns_arn}"
    "SNS_P3" : "${module.sns_budget_p3.sns_arn}"
  }
}

module "lambda_cost_alerter_forwarder_lambda_role" {
  source = "github.com/wearetechnative/terraform-aws-iam-role.git?ref=9229bbd0280807cbc49f194ff6d2741265dc108a"

  role_name = "lambda_cost_alerter_forwarder_lambda_role"
  role_path = "/cost_alerter/"

  aws_managed_policies = []
  customer_managed_policies = {
    "sqs_observability_receiver" : jsondecode(data.aws_iam_policy_document.sqs_observability_receiver.json)
  }

  trust_relationship = {
    "lambda" : { "identifier" : "lambda.amazonaws.com", "identifier_type" : "Service", "enforce_mfa" : false, "enforce_userprincipal" : false, "external_id" : null, "prevent_account_confuseddeputy" : false }
  }
}

resource "aws_sns_topic_subscription" "cost_alerter_forwarder_sns_source_p1" {
  topic_arn = module.sns_budget_p1.sns_arn
  protocol  = "lambda"
  endpoint  = module.cost_alerter_forwarder.lambda_function_arn

  redrive_policy = jsonencode({
    deadLetterTargetArn = var.sqs_dlq_arn
  })
}

resource "aws_sns_topic_subscription" "cost_alerter_forwarder_sns_source_p2" {
  topic_arn = module.sns_budget_p2.sns_arn
  protocol  = "lambda"
  endpoint  = module.cost_alerter_forwarder.lambda_function_arn

  redrive_policy = jsonencode({
    deadLetterTargetArn = var.sqs_dlq_arn
  })
}

resource "aws_sns_topic_subscription" "cost_alerter_forwarder_sns_source_p3" {
  topic_arn = module.sns_budget_p3.sns_arn
  protocol  = "lambda"
  endpoint  = module.cost_alerter_forwarder.lambda_function_arn

  redrive_policy = jsonencode({
    deadLetterTargetArn = var.sqs_dlq_arn
  })
}

resource "aws_lambda_permission" "cost_alerter_forwarder_sns_source_p1" {
  statement_id  = "AllowExecutionFromCostAlerterForwarderSNSSource"
  action        = "lambda:InvokeFunction"
  function_name = local.lambda_cost_alerter_forwarder_function_name
  principal     = "sns.amazonaws.com"
  source_arn    = module.sns_budget_p1.sns_arn

  depends_on = [
    module.cost_alerter_forwarder
  ]
}

resource "aws_lambda_permission" "cost_alerter_forwarder_sns_source_p2" {
  statement_id  = "AllowExecutionFromCostAlerterForwarderSNSSource"
  action        = "lambda:InvokeFunction"
  function_name = local.lambda_cost_alerter_forwarder_function_name
  principal     = "sns.amazonaws.com"
  source_arn    = module.sns_budget_p2.sns_arn

  depends_on = [
    module.cost_alerter_forwarder
  ]
}

resource "aws_lambda_permission" "cost_alerter_forwarder_sns_source_p3" {
  statement_id  = "AllowExecutionFromCostAlerterForwarderSNSSource"
  action        = "lambda:InvokeFunction"
  function_name = local.lambda_cost_alerter_forwarder_function_name
  principal     = "sns.amazonaws.com"
  source_arn    = module.sns_budget_p3.sns_arn

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
