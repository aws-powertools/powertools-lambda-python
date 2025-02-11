# Tracer constants
TRACER_CAPTURE_RESPONSE_ENV: str = "POWERTOOLS_TRACER_CAPTURE_RESPONSE"
TRACER_CAPTURE_ERROR_ENV: str = "POWERTOOLS_TRACER_CAPTURE_ERROR"
TRACER_DISABLED_ENV: str = "POWERTOOLS_TRACE_DISABLED"
XRAY_SDK_MODULE: str = "aws_xray_sdk"
XRAY_SDK_CORE_MODULE: str = "aws_xray_sdk.core"
XRAY_TRACE_ID_ENV: str = "_X_AMZN_TRACE_ID"
MIDDLEWARE_FACTORY_TRACE_ENV: str = "POWERTOOLS_TRACE_MIDDLEWARES"
INVALID_XRAY_NAME_CHARACTERS = r"[?;*()!$~^<>]"

# Logger constants
# maintenance: future major version should start having localized `constants.py` to ease future modularization
LOGGER_LOG_SAMPLING_RATE: str = "POWERTOOLS_LOGGER_SAMPLE_RATE"
LOGGER_LOG_EVENT_ENV: str = "POWERTOOLS_LOGGER_LOG_EVENT"
LOGGER_LOG_DEDUPLICATION_ENV: str = "POWERTOOLS_LOG_DEDUPLICATION_DISABLED"
LOGGER_LAMBDA_CONTEXT_KEYS = [
    "function_arn",
    "function_memory_size",
    "function_name",
    "function_request_id",
    "cold_start",
    "xray_trace_id",
]
# Mapping of Lambda log levels to Python logging levels
# https://docs.aws.amazon.com/lambda/latest/dg/configuration-logging.html#configuration-logging-log-levels
LAMBDA_ADVANCED_LOGGING_LEVELS = {
    None: None,
    "TRACE": "NOTSET",
    "DEBUG": "DEBUG",
    "INFO": "INFO",
    "WARN": "WARNING",
    "ERROR": "ERROR",
    "FATAL": "CRITICAL",
}
POWERTOOLS_LOG_LEVEL_ENV: str = "POWERTOOLS_LOG_LEVEL"
POWERTOOLS_LOG_LEVEL_LEGACY_ENV: str = "LOG_LEVEL"
LAMBDA_LOG_LEVEL_ENV: str = "AWS_LAMBDA_LOG_LEVEL"

# Metrics constants
METRICS_NAMESPACE_ENV: str = "POWERTOOLS_METRICS_NAMESPACE"
DATADOG_FLUSH_TO_LOG: str = "DD_FLUSH_TO_LOG"
SERVICE_NAME_ENV: str = "POWERTOOLS_SERVICE_NAME"
METRICS_DISABLED_ENV: str = "POWERTOOLS_METRICS_DISABLED"
# If the timestamp of log event is more than 2 hours in future, the log event is skipped.
# If the timestamp of log event is more than 14 days in past, the log event is skipped.
# See https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/AgentReference.html
EMF_MAX_TIMESTAMP_PAST_AGE = 14 * 24 * 60 * 60 * 1000  # 14 days
EMF_MAX_TIMESTAMP_FUTURE_AGE = 2 * 60 * 60 * 1000  # 2 hours

# Parameters constants
PARAMETERS_SSM_DECRYPT_ENV: str = "POWERTOOLS_PARAMETERS_SSM_DECRYPT"
PARAMETERS_MAX_AGE_ENV: str = "POWERTOOLS_PARAMETERS_MAX_AGE"

# Runtime and environment constants
LAMBDA_TASK_ROOT_ENV: str = "LAMBDA_TASK_ROOT"
SAM_LOCAL_ENV: str = "AWS_SAM_LOCAL"
CHALICE_LOCAL_ENV: str = "AWS_CHALICE_CLI_MODE"
LAMBDA_FUNCTION_NAME_ENV: str = "AWS_LAMBDA_FUNCTION_NAME"

# Debug constants
POWERTOOLS_DEV_ENV: str = "POWERTOOLS_DEV"
POWERTOOLS_DEBUG_ENV: str = "POWERTOOLS_DEBUG"

# JSON constants
PRETTY_INDENT: int = 4
COMPACT_INDENT: None = None

# Idempotency constants
IDEMPOTENCY_DISABLED_ENV: str = "POWERTOOLS_IDEMPOTENCY_DISABLED"
