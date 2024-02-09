from __future__ import annotations

from typing import Any, Dict, List, Union

from aws_lambda_powertools.shared.types import NotRequired, TypeAlias, TypedDict

LogRecord: TypeAlias = Union[Dict[str, Any], "PowertoolsLogRecord"]
LogStackTrace: TypeAlias = Union[Dict[str, Any], "PowertoolsStackTrace"]


class PowertoolsLogRecord(TypedDict):
    # Base fields (required)
    level: str
    location: str
    message: Dict[str, Any] | str | bool | List[Any]
    timestamp: str | int
    service: str

    # Fields from logger.inject_lambda_context
    cold_start: NotRequired[bool]
    function_name: NotRequired[str]
    function_memory_size: NotRequired[int]
    function_arn: NotRequired[str]
    function_request_id: NotRequired[str]
    # From logger.inject_lambda_context if AWS X-Ray is enabled
    xray_trace_id: NotRequired[str]

    # If sample_rate is defined
    sampling_rate: NotRequired[float]

    # From logger.set_correlation_id
    correlation_id: NotRequired[str]

    # Fields from logger.exception
    exception_name: NotRequired[str]
    exception: NotRequired[str]
    stack_trace: NotRequired[Dict[str, Any]]


class PowertoolsStackTrace(TypedDict):
    type: str
    value: str
    module: str
    frames: List[Dict[str, Any]]
