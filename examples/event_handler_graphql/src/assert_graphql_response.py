import json
from dataclasses import dataclass
from pathlib import Path

import pytest
from assert_graphql_response_module import Location, app  # instance of AppSyncResolver


@pytest.fixture
def lambda_context():
    @dataclass
    class LambdaContext:
        function_name: str = "test"
        memory_limit_in_mb: int = 128
        invoked_function_arn: str = "arn:aws:lambda:eu-west-1:123456789012:function:test"
        aws_request_id: str = "da658bd3-2d6f-4e7b-8ec2-937234644fdc"

    return LambdaContext()


def test_direct_resolver(lambda_context):
    # GIVEN
    fake_event = json.loads(Path("assert_graphql_response.json").read_text())

    # WHEN
    result: list[Location] = app(fake_event, lambda_context)

    # THEN
    assert result[0]["name"] == "Perkins-Reed"
