locals {
  lambda_cost_alerter_forwarder_function_name = "cost_alerter_forwarder"
}

module "cost_alerter_forwarder" {
  source = "git@github.com:TechNative-B-V/terraform-aws-module-lambda.git?ref=c63e985e3926e359612a6c398a635d6a9fea5653"

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
  }
}

module "lambda_cost_alerter_forwarder_lambda_role" {
  source = "git@github.com:TechNative-B-V/terraform-aws-module-iam-role.git?ref=81c45f4d87bace3e990e64b92030292ac2fc480c"

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

resource "aws_sns_topic_subscription" "cost_alerter_forwarder_sns_source" {
  topic_arn = module.sns_budget.sns_arn
  protocol  = "lambda"
  endpoint  = module.cost_alerter_forwarder.lambda_function_arn

  redrive_policy = jsonencode({
    deadLetterTargetArn = var.sqs_dlq_arn
  })
}

resource "aws_lambda_permission" "cost_alerter_forwarder_sns_source" {
  statement_id  = "AllowExecutionFromCostAlerterForwarderSNSSource"
  action        = "lambda:InvokeFunction"
  function_name = local.lambda_cost_alerter_forwarder_function_name
  principal     = "sns.amazonaws.com"
  source_arn    = module.sns_budget.sns_arn

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
