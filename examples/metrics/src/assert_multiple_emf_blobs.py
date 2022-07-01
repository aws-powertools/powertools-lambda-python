import json
from dataclasses import dataclass

import assert_multiple_emf_blobs_module
import pytest


@pytest.fixture
def lambda_context():
    @dataclass
    class LambdaContext:
        function_name: str = "test"
        memory_limit_in_mb: int = 128
        invoked_function_arn: str = "arn:aws:lambda:eu-west-1:809313241:function:test"
        aws_request_id: str = "52fdfc07-2182-154f-163f-5f0f9a621d72"

    return LambdaContext()


def capture_metrics_output_multiple_emf_objects(capsys):
    return [json.loads(line.strip()) for line in capsys.readouterr().out.split("\n") if line]


def test_log_metrics(capsys, lambda_context):
    assert_multiple_emf_blobs_module.lambda_handler({}, lambda_context)

    cold_start_blob, custom_metrics_blob = capture_metrics_output_multiple_emf_objects(capsys)

    # Since `capture_cold_start_metric` is used
    # we should have one JSON blob for cold start metric and one for the application
    assert cold_start_blob["ColdStart"] == [1.0]
    assert cold_start_blob["function_name"] == "test"

    assert "SuccessfulBooking" in custom_metrics_blob
