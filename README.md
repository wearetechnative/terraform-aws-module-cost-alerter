# Terraform AWS [Cost Alerter] ![](https://img.shields.io/github/workflow/status/wearetechnative/terraform-aws-module-cost-alerter/tflint.yaml?branch=main&style=plastic)

Automatically sets up and maintains per account cost usage alerts. Generally only works on management accounts.

- Automatically as in: Add alerts for new accounts and remove alerts for existing accounts.
- Usage defined as in: Costs controlled by usage only so excluding any tax and other incidental costs that are not related to use of AWS resources.
- Alert defined as: All alerts are being send to `var.master_observability_receiver_account_id` to end up in our LZ OpsGenie setup.

When alerts occur the user is expected to re-evaluate based on the budget created and manually increase the threshold by creating or adjusting an 
entry in the budgets_thresholds.json file that is passed to the budgets_thresholds variable from the clients management account's CodeCommit iac repository.


## budget_thresholds variable structure:
### Example:

```
{
    "Accounts" : {
        "Tracklib" : {                          <-- Account name needs to match account names in organizations
            "Id" :      "782826450191", 
            "Budget" :  "300.0"
        },
        "Tracklib Stage" : {
            "Id" :      "323546098264",
            "Budget" :  "11.0"
        },
        "Tracklib monitoring" : {
            "Id" :      "055036331264",
            "Budget" :  "15.0"
        }
    }

}
```
