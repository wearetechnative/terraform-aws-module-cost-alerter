module "sns_budget_p3" {
  source = "github.com/wearetechnative/terraform-aws-sns.git?ref=f1e48225d81f77372fd002d5d257f0aaa80075bb"
  
  name        = "sns_budget_p3"
  kms_key_arn = null
  policy_allowed = {
    budgets = {
      principal = {
        type       = "Service"
        identities = ["budgets.amazonaws.com"]
      }
      actions = ["SNS:Publish"]
    }
  }
}

module "sns_budget_p2" {
  source = "github.com/wearetechnative/terraform-aws-sns.git?ref=f1e48225d81f77372fd002d5d257f0aaa80075bb"
  
  name        = "sns_budget_p2"
  kms_key_arn = null
  policy_allowed = {
    budgets = {
      principal = {
        type       = "Service"
        identities = ["budgets.amazonaws.com"]
      }
      actions = ["SNS:Publish"]
    }
  }
}

module "sns_budget_p1" {
  source = "github.com/wearetechnative/terraform-aws-sns.git?ref=f1e48225d81f77372fd002d5d257f0aaa80075bb"
  
  name        = "sns_budget_p1"
  kms_key_arn = null
  policy_allowed = {
    budgets = {
      principal = {
        type       = "Service"
        identities = ["budgets.amazonaws.com"]
      }
      actions = ["SNS:Publish"]
    }
  }
}