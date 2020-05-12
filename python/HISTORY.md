# HISTORY 

## May 12th

**0.9.0**

* **Tracer**: Support for async functions in `Tracer` via `capture_method` decorator
* **Tracer**: Support for `aiohttp` via `aiohttp_trace_config` trace config
* **Tracer**: Support for patching specific modules via `patch_modules` param
* **Tracer**: Document escape hatch mechanisms via `tracer.provider`

## May 1st

**0.8.1**

* **Metrics**: Fix incorrect metric units enum values for `*PerSecond` e.g. CountPerSecond

## April 24th

**0.8.0**

* **Logger**: Introduces `Logger` class for stuctured logging as a replacement for `logger_setup`
* **Logger**: Introduces `Logger.inject_lambda_context` decorator as a replacement for `logger_inject_lambda_context`
* **Logger**: Raise `DeprecationWarning` exception for both `logger_setup`, `logger_inject_lambda_context`

## April 20th, 2020

**0.7.0**

* **Middleware factory**: Introduces Middleware Factory to build your own middleware via `lambda_handler_decorator`
* **Metrics**: Fixes metrics dimensions not being included correctly in EMF

## April 9th, 2020

**0.6.3**

* **Logger**: Fix `log_metrics` decorator logic not calling the decorated function, and exception handling

## April 8th, 2020

**0.6.1**

* **Metrics**: Introduces Metrics middleware to utilise CloudWatch Embedded Metric Format
* **Metrics**: Adds deprecation warning for `log_metrics`

## February 20th, 2020

**0.5.0**

* **Logger**: Introduces log sampling for debug - Thanks to [Danilo's contribution](https://github.com/awslabs/aws-lambda-powertools/pull/7)

## November 15th, 2019 

* Public beta release
