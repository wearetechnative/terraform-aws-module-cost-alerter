variable "master_observability_receiver_sqs_arn" {
  description = "AWS ID of the central management useraccount."
  type        = string
  default     = "arn:aws:sqs:eu-central-1:611159992020:sqs-opsgenie-lambda-queue-20220711145511259200000002"
}

variable "sqs_dlq_arn" {
  description = "SQS DLQ ARN for any messages / events that fail to process."
  type        = string
}

variable "kms_key_arn" {
  description = "KMS CMK used for any on-disk encryption supported."
  type        = string
}
