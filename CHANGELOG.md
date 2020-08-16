# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.1.2] - 2020-08-16
### Fixed
- **Docs**: Clarify confusion on Tracer reuse and `auto_patch=False` statement
- **Logger**: Autocomplete for log statements in PyCharm

## [1.1.1] - 2020-08-14
### Fixed
- **Logger**: Regression on `Logger` level not accepting `int` i.e. `Logger(level=logging.INFO)`

## [1.1.0] - 2020-08-14
### Added
- **Logger**: Support for logger inheritance with `child` parameter

### Fixed
- **Logger**: Log level is now case insensitive via params and env var

## [1.0.2] - 2020-07-16
### Fixed
- **Tracer**: Correct AWS X-Ray SDK dependency to support 2.5.0 and higher

## [1.0.1] - 2020-07-06
### Fixed
- **Logger**: Fix a bug with `inject_lambda_context` causing existing an Logger keys to be overriden if `structure_logs` was called before

## [1.0.0] - 2020-06-18
### Added
- **Metrics**: `add_metadata` method to add any metric metadata you'd like to ease finding metric related data via CloudWatch Logs
- Set status as General Availability

## [0.11.0] - 2020-06-08
### Added
- Imports can now be made from top level of module, e.g.: `from aws_lambda_powertools import Logger, Metrics, Tracer`

### Fixed
- **Metrics**: Fix a bug with Metrics causing an exception to be thrown when logging metrics if dimensions were not explicitly added.

### Changed
- **Metrics**: No longer throws exception by default in case no metrics are emitted when using the log_metrics decorator.

## [0.10.0] - 2020-06-08
### Added
- **Metrics**: `capture_cold_start_metric` parameter added to `log_metrics` decorator
- **Metrics**: Optional `namespace` and `service` parameters added to Metrics constructor to more closely resemble other core utils

### Changed
- **Metrics**: Default dimension is now created based on `service` parameter or `POWERTOOLS_SERVICE_NAME` env var

### Deprecated
- **Metrics**: `add_namespace` method deprecated in favor of using `namespace` parameter to Metrics constructor or `POWERTOOLS_METRICS_NAMESPACE` env var

## [0.9.5] - 2020-06-02
### Fixed
- **Metrics**: Coerce non-string dimension values to string
- **Logger**: Correct `cold_start`, `function_memory_size` values from string to bool and int respectively

## [0.9.4] - 2020-05-29
### Fixed
- **Metrics**: Fix issue where metrics were not correctly flushed, and cleared on every invocation

## [0.9.3] - 2020-05-16
### Fixed
- **Tracer**: Fix Runtime Error for nested sync due to incorrect loop usage

## [0.9.2] - 2020-05-14
### Fixed
- **Tracer**: Import aiohttp lazily so it's not a hard dependency

## [0.9.0] - 2020-05-12
### Added
- **Tracer**: Support for async functions in `Tracer` via `capture_method` decorator
- **Tracer**: Support for `aiohttp` via `aiohttp_trace_config` trace config
- **Tracer**: Support for patching specific modules via `patch_modules` param
- **Tracer**: Document escape hatch mechanisms via `tracer.provider`

## [0.8.1] - 2020-05-1
### Fixed
* **Metrics**: Fix metric unit casting logic if one passes plain string (value or key)
* **Metrics:**: Fix `MetricUnit` enum values for
    - `BytesPerSecond`
    - `KilobytesPerSecond`
    - `MegabytesPerSecond`
    - `GigabytesPerSecond`
    - `TerabytesPerSecond`
    - `BitsPerSecond`
    - `KilobitsPerSecond`
    - `MegabitsPerSecond`
    - `GigabitsPerSecond`
    - `TerabitsPerSecond`
    - `CountPerSecond`

## [0.8.0] - 2020-04-24
### Added
- **Logger**: Introduced `Logger` class for stuctured logging as a replacement for `logger_setup`
- **Logger**: Introduced `Logger.inject_lambda_context` decorator as a replacement for `logger_inject_lambda_context`

### Removed
- **Logger**: Raise `DeprecationWarning` exception for both `logger_setup`, `logger_inject_lambda_context`

## [0.7.0] - 2020-04-20
### Added
- **Middleware factory**: Introduced Middleware Factory to build your own middleware via `lambda_handler_decorator`

### Fixed
- **Metrics**: Fixed metrics dimensions not being included correctly in EMF

## [0.6.3] - 2020-04-09
### Fixed
- **Logger**: Fix `log_metrics` decorator logic not calling the decorated function, and exception handling

## [0.6.1] - 2020-04-08
### Added
- **Metrics**: Introduces Metrics middleware to utilise CloudWatch Embedded Metric Format

### Deprecated
- **Metrics**: Added deprecation warning for `log_metrics`

## [0.5.0] - 2020-02-20
### Added
- **Logger**: Introduced log sampling for debug - Thanks to [Danilo's contribution](https://github.com/awslabs/aws-lambda-powertools/pull/7)

## [0.1.0] - 2019-11-15
### Added
- Public beta release
