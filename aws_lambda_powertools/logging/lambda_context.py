from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from aws_lambda_powertools.utilities.typing import LambdaContext


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


def _unwrap_durable_context(context: Any) -> LambdaContext:
    """Unwrap Lambda Context from DurableContext if applicable.

    Parameters
    ----------
    context : object
        Lambda context object or DurableContext

    Returns
    -------
    LambdaContext
        The unwrapped Lambda context
    """
    # Check if this is a DurableContext by duck typing
    if hasattr(context, "lambda_context") and hasattr(context, "state"):
        return context.lambda_context

    return context


def build_lambda_context_model(context: Any) -> LambdaContextModel:
    """Captures Lambda function runtime info to be used across all log statements

    Parameters
    ----------
    context : object
        Lambda context object or DurableContext

    Returns
    -------
    LambdaContextModel
        Lambda context only with select fields
    """
    # Unwrap DurableContext if applicable
    lambda_context = _unwrap_durable_context(context)

    context = {
        "function_name": lambda_context.function_name,
        "function_memory_size": lambda_context.memory_limit_in_mb,
        "function_arn": lambda_context.invoked_function_arn,
        "function_request_id": lambda_context.aws_request_id,
    }

    return LambdaContextModel(**context)
