module "sns_budget" {
  source = "github.com/wearetechnative/terraform-aws-sns.git?ref=f1e48225d81f77372fd002d5d257f0aaa80075bb"

  name        = "sns_budget"
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
