from dataclasses import dataclass

import assert_alb_api_response_module
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
        "path": "/todos",
        "httpMethod": "GET",
        "headers": {"x-amzn-trace-id": "b25827e5-0e30-4d52-85a8-4df449ee4c5a"},
    }
    # Example of Application Load Balancer request event:
    # https://docs.aws.amazon.com/lambda/latest/dg/services-alb.html

    ret = assert_alb_api_response_module.lambda_handler(minimal_event, lambda_context)
    assert ret["statusCode"] == 200
    assert ret["body"] != ""
