import pytest


class LambdaContext:
    def __init__(self):
        self.function_name = "test-func"
        self.memory_limit_in_mb = 128
        self.invoked_function_arn = "arn:aws:lambda:eu-west-1:809313241234:function:test-func"
        self.aws_request_id = "52fdfc07-2182-154f-163f-5f0f9a621d72"

    def get_remaining_time_in_millis(self) -> int:
        return 1000


@pytest.fixture
def lambda_context():
    return LambdaContext()
