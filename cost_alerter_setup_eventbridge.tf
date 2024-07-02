resource "aws_cloudwatch_event_rule" "cost_alerter_setup" {
  name        = "cost_alerter_setup"
  description = "cost_alerter_setup"

  schedule_expression = "rate(60 minutes)"
}

resource "aws_cloudwatch_event_target" "cost_alerter_setup" {
  rule      = aws_cloudwatch_event_rule.cost_alerter_setup.name
  target_id = "CostAlerterSetup"
  arn       = module.cost_alerter_setup.lambda_function_arn

  dead_letter_config {
    arn = var.sqs_dlq_arn
  }
}

resource "aws_lambda_permission" "cost_alerter_setup" {
  statement_id  = "EventBridge60MinutesToCostAlerterSetup"
  action        = "lambda:InvokeFunction"
  function_name = local.lambda_cost_alerter_function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.cost_alerter_setup.arn

  depends_on = [
    module.cost_alerter_setup
  ]
}
