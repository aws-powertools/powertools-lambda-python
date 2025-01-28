terraform {
  required_version = "~> 1.0.5"
  required_providers {
    aws = "~> 3.50.0"
  }
}

provider "aws" {
  region = "{region}"
}

resource "aws_iam_role" "iam_for_lambda" {
  name = "iam_for_lambda"

  assume_role_policy = <<EOF
    {
        "Version": "2012-10-17",
        "Statement": [
        {
            "Action": "sts:AssumeRole",
            "Principal": {
            "Service": "lambda.amazonaws.com"
            },
            "Effect": "Allow"
        }
        ]
    }
    EOF
}

resource "aws_lambda_function" "test_lambda" {
  filename      = "lambda_function_payload.zip"
  function_name = "lambda_function_name"
  role          = aws_iam_role.iam_for_lambda.arn
  handler       = "index.test"
  runtime       = "python3.12"
  layers        = ["arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python312-x86_64:6"]

  source_code_hash = filebase64sha256("lambda_function_payload.zip")
}
