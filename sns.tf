module "sns_budget" {
  source = "git@github.com:wearetechnative/terraform-aws-sns.git?ref=9ba0b25ee91220deafa243d14b0ba935fad6cb85"
  
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
