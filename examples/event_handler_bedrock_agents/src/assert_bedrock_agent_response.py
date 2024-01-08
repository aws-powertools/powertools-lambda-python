from dataclasses import dataclass

import assert_bedrock_agent_response_module
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
        "apiPath": "/todos",
        "httpMethod": "GET",
        "inputText": "What is the current time?",
    }
    # Example of Bedrock Agent API request event:
    # https://docs.aws.amazon.com/bedrock/latest/userguide/agents-lambda.html#agents-lambda-input
    ret = assert_bedrock_agent_response_module.lambda_handler(minimal_event, lambda_context)
    assert ret["response"]["httpStatuScode"] == 200
    assert ret["response"]["responseBody"]["application/json"]["body"] != ""
