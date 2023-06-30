terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.0"
    }
  }
}

provider "aws" {
  region = "us-east-1" # Replace with your desired AWS region
}

resource "aws_dynamodb_table" "IdempotencyTable" {
  name         = "IdempotencyTable"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "id"
  attribute {
    name = "id"
    type = "S"
  }
  ttl {
    attribute_name = "expiration"
    enabled        = true
  }
}

resource "aws_lambda_function" "IdempotencyFunction" {
  function_name = "IdempotencyFunction"
  role          = aws_iam_role.IdempotencyFunctionRole.arn
  runtime       = "python3.10"
  handler       = "app.lambda_handler"
  filename      = "lambda.zip"

}

resource "aws_iam_role" "IdempotencyFunctionRole" {
  name = "IdempotencyFunctionRole"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = ""
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      },
    ]
  })
}

resource "aws_iam_policy" "LambdaDynamoDBPolicy" {
  name        = "LambdaDynamoDBPolicy"
  description = "IAM policy for Lambda function to access DynamoDB"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "AllowDynamodbReadWrite"
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:DeleteItem",
        ]
        Resource = aws_dynamodb_table.IdempotencyTable.arn
      },
    ]
  })
}

resource "aws_iam_role_policy_attachment" "IdempotencyFunctionRoleAttachment" {
  role       = aws_iam_role.IdempotencyFunctionRole.name
  policy_arn = aws_iam_policy.LambdaDynamoDBPolicy.arn
}
