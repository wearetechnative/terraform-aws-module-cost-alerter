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

variable "budget_thresholds" {
  description = "json budget thresholds for accounts with budget other than 10.0, structure: see README.md"
  default = {}
}

variable "client_name" {
  description = "Name of the Client"
  default = "Technative_LandingZone"
}

variable "notification_endpoint" {
  description = "Can be a SNS topic ARN or SQS queue URL."
  type        = string
}

variable "is_managed_service_client" {
  description = "Is the endpoint a a managed service client."
  type        = bool
  default     = false
}