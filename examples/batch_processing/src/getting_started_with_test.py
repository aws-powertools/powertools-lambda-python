import json
from dataclasses import dataclass
from pathlib import Path

import pytest
from getting_started_with_test_app import lambda_handler, processor


def load_event(path: Path):
    with path.open() as f:
        return json.load(f)


@pytest.fixture
def lambda_context():
    @dataclass
    class LambdaContext:
        function_name: str = "test"
        memory_limit_in_mb: int = 128
        invoked_function_arn: str = "arn:aws:lambda:eu-west-1:809313241:function:test"
        aws_request_id: str = "52fdfc07-2182-154f-163f-5f0f9a621d72"

    return LambdaContext()


@pytest.fixture()
def sqs_event():
    """Generates API GW Event"""
    return load_event(path=Path("events/sqs_event.json"))


def test_app_batch_partial_response(sqs_event, lambda_context):
    # GIVEN
    processor_result = processor  # access processor for additional assertions
    successful_record = sqs_event["Records"][0]
    failed_record = sqs_event["Records"][1]
    expected_response = {"batchItemFailures": [{"itemIdentifier": failed_record["messageId"]}]}

    # WHEN
    ret = lambda_handler(sqs_event, lambda_context)

    # THEN
    assert ret == expected_response
    assert len(processor_result.fail_messages) == 1
    assert processor_result.success_messages[0] == successful_record
