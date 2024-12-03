locals {
  lambda_cost_alerter_function_name = "cost_alerter_setup"
}

module "cost_alerter_setup" {
  source = "git@github.com:wearetechnative/terraform-aws-lambda.git?ref=ae0530a86c1eff7460d638e5ef885908ff5b8f88"

  name              = local.lambda_cost_alerter_function_name
  role_arn          = module.lambda_cost_alerter_setup_lambda_role.role_arn
  role_arn_provided = true

  handler                   = "lambda_function.lambda_handler"
  source_type               = "local"
  source_directory_location = "${path.module}/lambda_cost_alerter_setup"
  source_file_name          = null

  kms_key_arn = var.kms_key_arn
  sqs_dlq_arn = var.sqs_dlq_arn
  memory_size = 128
  timeout     = 300
  runtime     = "python3.9"

  environment_variables = {
    "BUDGET_SNS_TOPIC" : module.sns_budget.sns_arn
    "BUDGET_THRESHOLDS" : var.budget_thresholds
  }
}

module "lambda_cost_alerter_setup_lambda_role" {
  source = "  git@github.com:wearetechnative/terraform-aws-iam-role.git?ref=0fe916c27097706237692122e09f323f55e8237e"

  role_name = "lambda_cost_alerter_setup_lambda_role"
  role_path = "/cost_alerter/"

  aws_managed_policies = []
  customer_managed_policies = {
    "organizations_list_accounts" : jsondecode(data.aws_iam_policy_document.organizations_list_accounts.json)
    "budgets" : jsondecode(data.aws_iam_policy_document.budgets.json)
  }

  trust_relationship = {
    "lambda" : { "identifier" : "lambda.amazonaws.com", "identifier_type" : "Service", "enforce_mfa" : false, "enforce_userprincipal" : false, "external_id" : null, "prevent_account_confuseddeputy" : false }
  }
}

data "aws_iam_policy_document" "organizations_list_accounts" {
  statement {
    sid = "ListAccountsInOrganization"

    actions = ["organizations:ListAccounts"]

    resources = ["*"]
  }
}

data "aws_iam_policy_document" "budgets" {
  statement {
    sid = "ManageBudgets"

    actions = ["budgets:ViewBudget", "budgets:CreateBudget", "budgets:ModifyBudget"]

    resources = ["*"]
  }
}
