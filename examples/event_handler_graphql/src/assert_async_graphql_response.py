import json
from dataclasses import dataclass
from pathlib import Path
from typing import List

import pytest
from assert_async_graphql_response_module import (  # instance of AppSyncResolver
    Todo,
    app,
)


@pytest.fixture
def lambda_context():
    @dataclass
    class LambdaContext:
        function_name: str = "test"
        memory_limit_in_mb: int = 128
        invoked_function_arn: str = "arn:aws:lambda:eu-west-1:123456789012:function:test"
        aws_request_id: str = "da658bd3-2d6f-4e7b-8ec2-937234644fdc"

    return LambdaContext()


@pytest.mark.asyncio
async def test_async_direct_resolver(lambda_context):
    # GIVEN
    fake_event = json.loads(Path("assert_async_graphql_response.json").read_text())

    # WHEN
    result: List[Todo] = await app(fake_event, lambda_context)
    # alternatively, you can also run a sync test against `lambda_handler`
    # since `lambda_handler` awaits the coroutine to complete

    # THEN
    assert result[0]["userId"] == 1
    assert result[0]["id"] == 1
    assert result[0]["completed"] is False
