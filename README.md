# cost alerter

Automatically sets up and maintains per account cost usage alerts. Generally only works on management accounts.

- Automatically as in: Add alerts for new accounts and remove alerts for existing accounts.
- Usage defined as in: Costs controlled by usage only so excluding any tax and other incidental costs that are not related to use of AWS resources.
- Alert defined as: All alerts are being send to `var.master_observability_receiver_account_id` to end up in our LZ OpsGenie setup.

When alerts occur the user is expected to re-evaluate based on the budget created and manually increase the threshold.

## When removing this module

Delete any budget alerts manually.
