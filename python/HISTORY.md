# HISTORY 

## May 1st

**0.8.1**

* Fix metric unit casting logic if one passes plain string (value or key)
* Fix `MetricUnit` enum values for
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

## April 24th

**0.8.0**

* Introduces `Logger` for stuctured logging as a replacement for `logger_setup`
* Introduces `Logger.inject_lambda_context` decorator as a replacement for `logger_inject_lambda_context`
* Raise `DeprecationWarning` exception for both `logger_setup`, `logger_inject_lambda_context`

## April 20th, 2020

**0.7.0**

* Introduces Middleware Factory to build your own middleware
* Fixes Metrics dimensions not being included correctly in EMF

## April 9th, 2020

**0.6.3**

* Fix `log_metrics` decorator logic not calling the decorated function, and exception handling

## April 8th, 2020

**0.6.1**

* Introduces Metrics middleware to utilise CloudWatch Embedded Metric Format
* Adds deprecation warning for `log_metrics`

## February 20th, 2020

**0.5.0**

* Introduces log sampling for debug - Thanks to [Danilo's contribution](https://github.com/awslabs/aws-lambda-powertools/pull/7)

## November 15th, 2019 

* Public beta release
