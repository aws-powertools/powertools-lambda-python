terraform {
  required_version = "~> 0.13"
  required_providers {
    aws = "~> 3.50.0"
  }
}

provider "aws" {
  region  = "us-east-1"
}

resource "aws_serverlessapplicationrepository_cloudformation_stack" "deploy_sar_stack" {
  name = "aws-lambda-powertools-python-layer"

  application_id   = data.aws_serverlessapplicationrepository_application.sar_app.application_id
  semantic_version = data.aws_serverlessapplicationrepository_application.sar_app.semantic_version
  capabilities = [
    "CAPABILITY_IAM",
    "CAPABILITY_NAMED_IAM"
  ]
}

data "aws_serverlessapplicationrepository_application" "sar_app" {
  application_id   = "arn:aws:serverlessrepo:eu-west-1:057560766410:applications/aws-lambda-powertools-python-layer"
  semantic_version = var.aws_powertools_version
}

variable "aws_powertools_version" {
  type        = string
  default     = "1.25.10"
  description = "The AWS Powertools release version"
}

output "deployed_powertools_sar_version" {
  value = data.aws_serverlessapplicationrepository_application.sar_app.semantic_version
}

# Fetch Lambda Powertools Layer ARN from deployed SAR App
output "aws_lambda_powertools_layer_arn" {
  value = aws_serverlessapplicationrepository_cloudformation_stack.deploy_sar_stack.outputs.LayerVersionArn
}
