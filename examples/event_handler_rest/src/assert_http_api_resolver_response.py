from dataclasses import dataclass

import assert_http_api_response_module
import pytest


@pytest.fixture
def lambda_context():
    @dataclass
    class LambdaContext:
        function_name: str = "test"
        memory_limit_in_mb: int = 128
        invoked_function_arn: str = "arn:aws:lambda:eu-west-1:123456789012:function:test"
        aws_request_id: str = "da658bd3-2d6f-4e7b-8ec2-937234644fdc"

    return LambdaContext()


def test_lambda_handler(lambda_context):
    minimal_event = {
        "rawPath": "/todos",
        "requestContext": {
            "requestContext": {"requestId": "227b78aa-779d-47d4-a48e-ce62120393b8"},  # correlation ID
            "http": {
                "method": "GET",
            },
            "stage": "$default",
        },
    }
    # Example of API Gateway HTTP API request event:
    # https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-develop-integrations-lambda.html

    ret = assert_http_api_response_module.lambda_handler(minimal_event, lambda_context)
    assert ret["statusCode"] == 200
    assert ret["body"] != ""
