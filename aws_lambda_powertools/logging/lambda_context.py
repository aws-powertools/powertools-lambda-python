from typing import Any


class LambdaContextModel:
    """A handful of Lambda Runtime Context fields

    Full Lambda Context object: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    Parameters
    ----------
    function_name: str
        Lambda function name, by default "UNDEFINED"
        e.g. "test"
    function_memory_size: int
        Lambda function memory in MB, by default 128
    function_arn: str
        Lambda function ARN, by default "UNDEFINED"
        e.g. "arn:aws:lambda:eu-west-1:809313241:function:test"
    function_request_id: str
        Lambda function unique request id, by default "UNDEFINED"
        e.g. "52fdfc07-2182-154f-163f-5f0f9a621d72"
    """

    def __init__(
        self,
        function_name: str = "UNDEFINED",
        function_memory_size: int = 128,
        function_arn: str = "UNDEFINED",
        function_request_id: str = "UNDEFINED",
    ):
        self.function_name = function_name
        self.function_memory_size = function_memory_size
        self.function_arn = function_arn
        self.function_request_id = function_request_id


def build_lambda_context_model(context: Any) -> LambdaContextModel:
    """Captures Lambda function runtime info to be used across all log statements

    Parameters
    ----------
    context : object
        Lambda context object

    Returns
    -------
    LambdaContextModel
        Lambda context only with select fields
    """

    context = {
        "function_name": context.function_name,
        "function_memory_size": context.memory_limit_in_mb,
        "function_arn": context.invoked_function_arn,
        "function_request_id": context.aws_request_id,
    }

    return LambdaContextModel(**context)
