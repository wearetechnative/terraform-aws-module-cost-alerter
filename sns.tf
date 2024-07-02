module "sns_budget" {
  source = "git@github.com:TechNative-B-V/terraform-aws-module-sns.git?ref=fbee551a075c5dc895eb0ad36ed722d6292c0388"

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
