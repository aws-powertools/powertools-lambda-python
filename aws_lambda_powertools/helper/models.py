"""Collection of classes as models and builder functions
that provide classes as data representation for
key data used in more than one place.
"""

from enum import Enum
from typing import Union


class LambdaContextModel:
    """A handful of Lambda Runtime Context fields

    Full Lambda Context object: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html

    NOTE
    ----

    Originally, memory_size is `int` but we cast to `str` in this model
    due to aws_lambda_logging library use of `%` during formatting
    Ref: https://gitlab.com/hadrien/aws_lambda_logging/blob/master/aws_lambda_logging.py#L47

    Parameters
    ----------
    function_name: str
        Lambda function name, by default "UNDEFINED"
        e.g. "test"
    function_memory_size: str
        Lambda function memory in MB, by default "UNDEFINED"
        e.g. "128"
        casting from int to str due to aws_lambda_logging using `%` when enumerating fields
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
        function_memory_size: str = "UNDEFINED",
        function_arn: str = "UNDEFINED",
        function_request_id: str = "UNDEFINED",
    ):
        self.function_name = function_name
        self.function_memory_size = function_memory_size
        self.function_arn = function_arn
        self.function_request_id = function_request_id


def build_lambda_context_model(context: object) -> LambdaContextModel:
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


class MetricUnit(Enum):
    Seconds = "Seconds"
    Microseconds = "Microseconds"
    Milliseconds = "Milliseconds"
    Bytes = "Bytes"
    Kilobytes = "Kilobytes"
    Megabytes = "Megabytes"
    Gigabytes = "Gigabytes"
    Terabytes = "Terabytes"
    Bits = "Bits"
    Kilobits = "Kilobits"
    Megabits = "Megabits"
    Gigabits = "Gigabits"
    Terabits = "Terabits"
    Percent = "Percent"
    Count = "Count"
    BytesPerSecond = "Bytes/Second"
    KilobytesPerSecond = "Kilobytes/Second"
    MegabytesPerSecond = "Megabytes/Second"
    GigabytesPerSecond = "Gigabytes/Second"
    TerabytesPerSecond = "Terabytes/Second"
    BitsPerSecond = "Bits/Second"
    KilobitsPerSecond = "Kilobits/Second"
    MegabitsPerSecond = "Megabits/Second"
    GigabitsPerSecond = "Gigabits/Second"
    TerabitsPerSecond = "Terabits/Second"
    CountPerSecond = "Count/Second"


def build_metric_unit_from_str(unit: Union[str, MetricUnit]) -> MetricUnit:
    """Builds correct metric unit value from string or return Count as default

    Parameters
    ----------
    unit : str, MetricUnit
        metric unit

    Returns
    -------
    MetricUnit
        Metric Unit enum from string value or MetricUnit.Count as a default
    """
    if isinstance(unit, MetricUnit):
        return unit

    if isinstance(unit, str):
        unit = unit.lower().capitalize()

    metric_unit = None

    try:
        metric_unit = MetricUnit[unit]
    except (TypeError, KeyError):
        metric_units = [units for units, _ in MetricUnit.__members__.items()]
        raise ValueError(f"Invalid Metric Unit - Received {unit}. Value Metric Units are {metric_units}")

    return metric_unit
