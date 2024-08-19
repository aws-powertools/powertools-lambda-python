from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, TypedDict, Union

if TYPE_CHECKING:
    from typing_extensions import NotRequired, TypeAlias


class PowertoolsLogRecord(TypedDict):
    # Base fields (required)
    level: str
    location: str
    message: dict[str, Any] | str | bool | list[Any]
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
    stack_trace: NotRequired[dict[str, Any]]


class PowertoolsStackTrace(TypedDict):
    type: str
    value: str
    module: str
    frames: list[dict[str, Any]]


LogRecord: TypeAlias = Union[Dict[str, Any], PowertoolsLogRecord]
LogStackTrace: TypeAlias = Union[Dict[str, Any], PowertoolsStackTrace]
