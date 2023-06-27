from dataclasses import dataclass

import app_test_dynamodb_local
import boto3
import pytest


@pytest.fixture
def lambda_context():
    @dataclass
    class LambdaContext:
        function_name: str = "test"
        memory_limit_in_mb: int = 128
        invoked_function_arn: str = "arn:aws:lambda:eu-west-1:809313241:function:test"
        aws_request_id: str = "52fdfc07-2182-154f-163f-5f0f9a621d72"

        def get_remaining_time_in_millis(self) -> int:
            return 5

    return LambdaContext()


def test_idempotent_lambda(lambda_context):
    # Configure the boto3 to use the endpoint for the DynamoDB Local instance
    dynamodb_local_client = boto3.client("dynamodb", endpoint_url="http://localhost:8000")
    app_test_dynamodb_local.persistence_layer.client = dynamodb_local_client

    # If desired, you can use a different DynamoDB Local table name than what your code already uses
    # app.persistence_layer.table_name = "another table name" # noqa: ERA001

    result = app_test_dynamodb_local.handler({"testkey": "testvalue"}, lambda_context)
    assert result["payment_id"] == 12345
