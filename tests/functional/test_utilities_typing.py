from aws_lambda_powertools.utilities.typing import LambdaContext


def test_typing():
    context = LambdaContext()
    assert context.get_remaining_time_in_millis() == 0
