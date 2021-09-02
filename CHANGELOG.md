# Changelog

All notable changes to this project will be documented in this file.

This project follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format for changes and adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

## 1.20.2 - 2021-09-02

### Bug Fixes

* **event-handler:** fix issue with strip_prefixes and root level resolvers ([#646](https://github.com/awslabs/aws-lambda-powertools-python/issues/646))

### Maintenance

* **deps:** bump boto3 from 1.18.26 to 1.18.32 ([#663](https://github.com/awslabs/aws-lambda-powertools-python/issues/663))
* **deps-dev:** bump mkdocs-material from 7.2.4 to 7.2.6 ([#665](https://github.com/awslabs/aws-lambda-powertools-python/issues/665))
* **deps-dev:** bump pytest from 6.2.4 to 6.2.5 ([#662](https://github.com/awslabs/aws-lambda-powertools-python/issues/662))
* **deps-dev:** bump mike from 0.6.0 to 1.0.1 ([#453](https://github.com/awslabs/aws-lambda-powertools-python/issues/453))
* **license:** add third party license to pyproject.toml ([#641](https://github.com/awslabs/aws-lambda-powertools-python/issues/641))

## 1.20.1 - 2021-08-22

### Bug Fixes

* **idempotency:** sorting keys before hashing ([#639](https://github.com/awslabs/aws-lambda-powertools-python/issues/639))

### Maintenance

* markdown linter fixes ([#636](https://github.com/awslabs/aws-lambda-powertools-python/issues/636))
* setup codespaces ([#637](https://github.com/awslabs/aws-lambda-powertools-python/issues/637))
* **license:** add third party license ([#635](https://github.com/awslabs/aws-lambda-powertools-python/issues/635))

## 1.20.0 - 2021-08-21

## Bug Fixes

* **api-gateway:** HTTP API strip stage name from request path ([#622](https://github.com/awslabs/aws-lambda-powertools-python/issues/622))

### Code Refactoring

* **event-handler:** match to match_results; 3.10 new keyword ([#616](https://github.com/awslabs/aws-lambda-powertools-python/issues/616))

### Documentation

* **data-classes:** make authorizer concise; use enum ([#630](https://github.com/awslabs/aws-lambda-powertools-python/issues/630))
* **feature-flags:** correct link and json examples ([#605](https://github.com/awslabs/aws-lambda-powertools-python/issues/605))
* **data-class:** fix invalid syntax in new AppSync Authorizer
* **api-gateway:** add new API mapping support

### Features

* **data-classes:** authorizer for API Gateway HTTP and REST API ([#620](https://github.com/awslabs/aws-lambda-powertools-python/issues/620))
* **data-classes:** new data_as_bytes property in KinesisStreamRecordPayload ([#628](https://github.com/awslabs/aws-lambda-powertools-python/issues/628))
* **data-classes:** AppSync Lambda authorizer event ([#610](https://github.com/awslabs/aws-lambda-powertools-python/issues/610))
* **event-handler:** prefixes to strip for custom domain mapping paths ([#579](https://github.com/awslabs/aws-lambda-powertools-python/issues/579))
* **general:** support for Python 3.9 ([#626](https://github.com/awslabs/aws-lambda-powertools-python/issues/626))
* **idempotency:** support for any synchronous function ([#625](https://github.com/awslabs/aws-lambda-powertools-python/issues/625))

### Maintenance

* **actions:** include new labels
* **api-docs:** enable allow_reuse to fix the docs ([#612](https://github.com/awslabs/aws-lambda-powertools-python/issues/612))
* **deps:** bump boto3 from 1.18.25 to 1.18.26 ([#627](https://github.com/awslabs/aws-lambda-powertools-python/issues/627))
* **deps:** bump boto3 from 1.18.24 to 1.18.25 ([#623](https://github.com/awslabs/aws-lambda-powertools-python/issues/623))
* **deps:** bump boto3 from 1.18.22 to 1.18.24 ([#619](https://github.com/awslabs/aws-lambda-powertools-python/issues/619))
* **deps:** bump boto3 from 1.18.17 to 1.18.21 ([#608](https://github.com/awslabs/aws-lambda-powertools-python/issues/608))
* **deps:** bump boto3 from 1.18.21 to 1.18.22 ([#614](https://github.com/awslabs/aws-lambda-powertools-python/issues/614))
* **deps-dev:** bump flake8-comprehensions from 3.5.0 to 3.6.0 ([#609](https://github.com/awslabs/aws-lambda-powertools-python/issues/609))
* **deps-dev:** bump flake8-comprehensions from 3.6.0 to 3.6.1 ([#615](https://github.com/awslabs/aws-lambda-powertools-python/issues/615))
* **deps-dev:** bump mkdocs-material from 7.2.3 to 7.2.4 ([#607](https://github.com/awslabs/aws-lambda-powertools-python/issues/607))
* **docs:** correct markdown based on markdown lint ([#603](https://github.com/awslabs/aws-lambda-powertools-python/issues/603))
* **shared:** fix cyclic import & refactor data extraction fn ([#613](https://github.com/awslabs/aws-lambda-powertools-python/issues/613))

## 1.19.0 - 2021-08-11

### Bug Fixes

* **deps:** bump poetry to latest ([#592](https://github.com/awslabs/aws-lambda-powertools-python/issues/592))
* **feature-flags:** bug handling multiple conditions ([#599](https://github.com/awslabs/aws-lambda-powertools-python/issues/599))
* **parser:** API Gateway WebSocket validation under check_message_id; plus some housekeeping ([#553](https://github.com/awslabs/aws-lambda-powertools-python/issues/553))
* **feature-toggles:** correct cdk example ([#601](https://github.com/awslabs/aws-lambda-powertools-python/issues/601))

### Code Refactoring

* **feature-flags:** add debug statements for all feature evaluations ([#590](https://github.com/awslabs/aws-lambda-powertools-python/issues/590))
* **feature-flags:** optimize UX and maintenance ([#563](https://github.com/awslabs/aws-lambda-powertools-python/issues/563))

### Documentation

* **event-handler:** new custom serializer option
* **feature-flags:** create concrete documentation ([#594](https://github.com/awslabs/aws-lambda-powertools-python/issues/594))
* **feature-flags:** correct docs and typing ([#588](https://github.com/awslabs/aws-lambda-powertools-python/issues/588))
* **parameters:** auto-transforming values based on suffix ([#573](https://github.com/awslabs/aws-lambda-powertools-python/issues/573))
* **readme:** add code coverage badge ([#577](https://github.com/awslabs/aws-lambda-powertools-python/issues/577))
* **tracer:** update wording that it auto-disables on non-Lambda env
* **feature-flags:** fix SAM infra, convert CDK to Python
* **feature-flags:** fix sample feature name in evaluate method
* **feature-flags:** add guidance when to use vs env vars vs parameters
### Features

* **api-gateway:** add support for custom serializer ([#568](https://github.com/awslabs/aws-lambda-powertools-python/issues/568))
* **data-classes:** decode json_body if based64 encoded ([#560](https://github.com/awslabs/aws-lambda-powertools-python/issues/560))
* **feature-flags:** Add not_in action and rename contains to in ([#589](https://github.com/awslabs/aws-lambda-powertools-python/issues/589))
* **params:** expose params `max_age`, `raise_on_transform_error` to high level functions ([#567](https://github.com/awslabs/aws-lambda-powertools-python/issues/567))
* **tracer:** auto-disable tracer for non-Lambda environments to ease testing ([#598](https://github.com/awslabs/aws-lambda-powertools-python/issues/598))

### Maintenance

* **deps:** bump boto3 from 1.18.1 to 1.18.15 ([#591](https://github.com/awslabs/aws-lambda-powertools-python/issues/591))
* **deps:** bump codecov/codecov-action from 2.0.1 to 2.0.2 ([#558](https://github.com/awslabs/aws-lambda-powertools-python/issues/558))
* **deps:** bump boto3 from 1.18.15 to 1.18.17 ([#597](https://github.com/awslabs/aws-lambda-powertools-python/issues/597))
* **deps-dev:** bump mkdocs-material from 7.2.2 to 7.2.3 ([#596](https://github.com/awslabs/aws-lambda-powertools-python/issues/596))
* **deps-dev:** bump mkdocs-material from 7.2.1 to 7.2.2 ([#582](https://github.com/awslabs/aws-lambda-powertools-python/issues/582))
* **deps-dev:** bump pdoc3 from 0.9.2 to 0.10.0 ([#584](https://github.com/awslabs/aws-lambda-powertools-python/issues/584))
* **deps-dev:** bump isort from 5.9.2 to 5.9.3 ([#574](https://github.com/awslabs/aws-lambda-powertools-python/issues/574))
* **deps-dev:** bump mkdocs-material from 7.2.0 to 7.2.1 ([#566](https://github.com/awslabs/aws-lambda-powertools-python/issues/566))
* **deps-dev:** bump mkdocs-material from 7.1.11 to 7.2.0 ([#551](https://github.com/awslabs/aws-lambda-powertools-python/issues/551))
* **deps-dev:** bump flake8-black from 0.2.1 to 0.2.3 ([#541](https://github.com/awslabs/aws-lambda-powertools-python/issues/541))
## 1.18.1 - 2021-07-23

### Bug Fixes

* **api-gateway:** route regression for non-word and unsafe URI chars ([#556](https://github.com/awslabs/aws-lambda-powertools-python/issues/556))

## 1.18.0 - 2021-07-20

### Bug Fixes

* **api-gateway:** non-greedy route pattern regex which incorrectly mapped certain route params to function params ([#533](https://github.com/awslabs/aws-lambda-powertools-python/issues/533))
* **api-gateway:** incorrect plain text mimetype constant [#506](https://github.com/awslabs/aws-lambda-powertools-python/issues/506)
* **data-classes:** include milliseconds in scalar types to correctly align with AppSync scalars ([#504](https://github.com/awslabs/aws-lambda-powertools-python/issues/504))
* **mypy:** addresses lack of optional types ([#521](https://github.com/awslabs/aws-lambda-powertools-python/issues/521))
* **parser:** make ApiGateway version, authorizer fields optional ([#532](https://github.com/awslabs/aws-lambda-powertools-python/issues/532))
* **tracer:** mypy generic to preserve decorated method signature ([#529](https://github.com/awslabs/aws-lambda-powertools-python/issues/529))

### Code Refactoring

* **feature-toggles:** code coverage and housekeeping ([#530](https://github.com/awslabs/aws-lambda-powertools-python/issues/530))

### Documentation

* **api-gateway:** new HTTP service error exceptions ([#546](https://github.com/awslabs/aws-lambda-powertools-python/issues/546))
* **logger:** new get_correlation_id method ([#545](https://github.com/awslabs/aws-lambda-powertools-python/issues/545))

### Features

* **api-gateway:** add debug mode ([#507](https://github.com/awslabs/aws-lambda-powertools-python/issues/507))
* **api-gateway:** add common HTTP service errors ([#506](https://github.com/awslabs/aws-lambda-powertools-python/issues/506))
* **event-handler:** Support AppSyncResolverEvent subclassing ([#526](https://github.com/awslabs/aws-lambda-powertools-python/issues/526))
* **feat-toggle:** New simple feature toggles rule engine (WIP) ([#494](https://github.com/awslabs/aws-lambda-powertools-python/issues/494))
* **logger:** add get_correlation_id method ([#516](https://github.com/awslabs/aws-lambda-powertools-python/issues/516))

### Maintenance

* **mypy:** add mypy support to makefile ([#508](https://github.com/awslabs/aws-lambda-powertools-python/issues/508))
* **deps:** bump codecov/codecov-action from 1 to 2.0.1 ([#539](https://github.com/awslabs/aws-lambda-powertools-python/issues/539))
* **deps:** bump boto3 from 1.18.0 to 1.18.1 ([#528](https://github.com/awslabs/aws-lambda-powertools-python/issues/528))
* **deps:** bump boto3 from 1.17.110 to 1.18.0 ([#527](https://github.com/awslabs/aws-lambda-powertools-python/issues/527))
* **deps:** bump boto3 from 1.17.102 to 1.17.110 ([#523](https://github.com/awslabs/aws-lambda-powertools-python/issues/523))
* **deps-dev:** bump mkdocs-material from 7.1.10 to 7.1.11 ([#542](https://github.com/awslabs/aws-lambda-powertools-python/issues/542))
* **deps-dev:** bump mkdocs-material from 7.1.9 to 7.1.10 ([#522](https://github.com/awslabs/aws-lambda-powertools-python/issues/522))
* **deps-dev:** bump isort from 5.9.1 to 5.9.2 ([#514](https://github.com/awslabs/aws-lambda-powertools-python/issues/514))
* **event-handler:** adjusts API Gateway/ALB service errors exception docstrings to not confuse AppSync customers

## 1.17.1 - 2021-07-02

### Bug Fixes

* **Validator:** Handle built-in custom formats like `date-time` when type is `string` ([#498](https://github.com/awslabs/aws-lambda-powertools-python/issues/498))

### Documentation

* **Layers:** Add Layers example for Serverless framework & CDK ([#500](https://github.com/awslabs/aws-lambda-powertools-python/issues/500))
* **Misc.:** Enable dark mode switch ([#471](https://github.com/awslabs/aws-lambda-powertools-python/issues/471))
* **Tracer:** Additional scenario when to disable auto-capture for responses larger than 64K ([#499](https://github.com/awslabs/aws-lambda-powertools-python/issues/499))

### Maintenance

* **deps:** bump boto3 from 1.17.101 to 1.17.102 ([#493](https://github.com/awslabs/aws-lambda-powertools-python/issues/493))
* **deps:** bump boto3 from 1.17.91 to 1.17.101 ([#490](https://github.com/awslabs/aws-lambda-powertools-python/issues/490))
* **deps:** bump email-validator from 1.1.2 to 1.1.3 ([#478](https://github.com/awslabs/aws-lambda-powertools-python/issues/478))
* **deps:** bump boto3 from 1.17.89 to 1.17.91 ([#473](https://github.com/awslabs/aws-lambda-powertools-python/issues/473))
* **deps-dev:** bump flake8-eradicate from 1.0.0 to 1.1.0 ([#492](https://github.com/awslabs/aws-lambda-powertools-python/issues/492))
* **deps-dev:** bump isort from 5.8.0 to 5.9.1 ([#487](https://github.com/awslabs/aws-lambda-powertools-python/issues/487))
* **deps-dev:** bump mkdocs-material from 7.1.7 to 7.1.9 ([#491](https://github.com/awslabs/aws-lambda-powertools-python/issues/491))

## 1.17.0 - 2021-06-08

### Added

* **Documentation**: Include new public roadmap ([#452](https://github.com/awslabs/aws-lambda-powertools-python/issues/452))
* **Documentation**: Remove old todo in idempotency docs
* **Data classes:** New `AttributeValueType` to get type and value from data in `DynamoDBStreamEvent` ([#462](https://github.com/awslabs/aws-lambda-powertools-python/issues/462))
* **Data classes:** New decorator `event_source` to instantiate data_classes ([#442](https://github.com/awslabs/aws-lambda-powertools-python/issues/442))
* **Logger:** New `clear_state` parameter to clear previously added custom keys upon invocation ([#467](https://github.com/awslabs/aws-lambda-powertools-python/issues/467))
* **Parser:** Support for API Gateway HTTP API [#434](https://github.com/awslabs/aws-lambda-powertools-python/issues/434) ([#441](https://github.com/awslabs/aws-lambda-powertools-python/issues/441))

### Maintenance

* **deps**: bump xenon from 0.7.1 to 0.7.3 ([#446](https://github.com/awslabs/aws-lambda-powertools-python/issues/446))
* assited changelog pre-generation, auto-label PR ([#443](https://github.com/awslabs/aws-lambda-powertools-python/issues/443))
* enable dependabot for dep upgrades ([#444](https://github.com/awslabs/aws-lambda-powertools-python/issues/444))
* enable mergify ([#450](https://github.com/awslabs/aws-lambda-powertools-python/issues/450))
* **deps**: bump mkdocs-material from 7.1.5 to 7.1.6 ([#451](https://github.com/awslabs/aws-lambda-powertools-python/issues/451))
* **deps**: bump boto3 from 1.17.78 to 1.17.84 ([#449](https://github.com/awslabs/aws-lambda-powertools-python/issues/449))
* update mergify to require approval on dependabot ([#456](https://github.com/awslabs/aws-lambda-powertools-python/issues/456))
* **deps**: bump actions/setup-python from 1 to 2.2.2 ([#445](https://github.com/awslabs/aws-lambda-powertools-python/issues/445))
* **deps:** bump boto3 from 1.17.87 to 1.17.88 ([#463](https://github.com/awslabs/aws-lambda-powertools-python/issues/463))
* **deps:** bump boto3 from 1.17.88 to 1.17.89 ([#466](https://github.com/awslabs/aws-lambda-powertools-python/issues/466))
* **deps:** bump boto3 from 1.17.84 to 1.17.85 ([#455](https://github.com/awslabs/aws-lambda-powertools-python/issues/455))
* **deps:** bump boto3 from 1.17.85 to 1.17.86 ([#458](https://github.com/awslabs/aws-lambda-powertools-python/issues/458))
* **deps:** bump boto3 from 1.17.86 to 1.17.87 ([#459](https://github.com/awslabs/aws-lambda-powertools-python/issues/459))
* **deps-dev:** bump mkdocs-material from 7.1.6 to 7.1.7 ([#464](https://github.com/awslabs/aws-lambda-powertools-python/issues/464))
* **deps-dev:** bump pytest-cov from 2.12.0 to 2.12.1 ([#454](https://github.com/awslabs/aws-lambda-powertools-python/issues/454))
* **mergify:** disable check for matrix jobs
* **mergify:** use job name to match GH Actions

## 1.16.1 - 2021-05-23

### Fixed

* **Parser**: Upgrade Pydantic to 1.8.2 due to CVE-2021-29510

## 1.16.0 - 2021-05-17
### Features
- **data-classes(API Gateway, ALB):** New method to decode base64 encoded body ([#425](https://github.com/awslabs/aws-lambda-powertools-python/issues/425))
- **data-classes(CodePipeline):** Support for CodePipeline job event and methods to handle artifacts more easily ([#416](https://github.com/awslabs/aws-lambda-powertools-python/issues/416))

## 1.15.1 - 2021-05-13

### Fixed

* **Logger**: Fix a regression with the `%s` operator

## 1.15.0 - 2021-05-06

### Added

* **Event handlers**: New API Gateway and ALB utility to reduce routing boilerplate and more
* **Documentation**: Logger enhancements such as bring your own formatter, handler, UTC support, and testing for Python 3.6
* **Parser**: Support for API Gateway REST Proxy event and envelope
* **Logger**: Support for bringing custom formatter, custom handler, custom JSON serializer and deserializer, UTC support, expose `LambdaPowertoolsFormatter`
* **Metrics**: Support for persisting default dimensions that should always be added

### Fixed

* **Documentation**: Fix highlights, Parser types
* **Validator**: Fix event type annotations for `validate` standalone function
* **Parser**: Improve and fix types
* **Internal**: Remove X-Ray SDK version pinning as serialization regression has been fixed in 2.8.0
* **Internal**: Latest documentation correctly includes a copy of API docs reference

## 1.14.0 - 2021-04-09

### Added

* **Event handlers**: New core utility to easily handle incoming requests tightly integrated with Data Classes; AppSync being the first as we gauge from the community what additional ones would be helpful
* **Documentation**: Enabled versioning to access docs on a per release basis or staging docs (`develop` branch)
* **Documentation**: Links now open in a new tab and improved snippet line highlights
* **Documentation(validation)**: JSON Schema snippets and more complete examples
* **Documentation(idempotency)**: Table with expected configuration values for hash key and TTL attribute name when using the default behaviour
* **Documentation(logger)**: New example on how to set logging record timestamps in UTC
* **Parser(S3)**: Support for the new S3 Object Lambda Event model (`S3ObjectLambdaEvent`)
* **Parameters**: Support for DynamoDB Local via `endpoint_url` parameter, including docs
* **Internal**: Include `make pr` in pre-commit hooks when contributing to shorten feedback loop on pre-commit specific linting

### Fixed

* **Parser**: S3Model now supports keys with 0 length
* **Tracer**: Lock X-Ray SDK to 2.6.0 as there's been a regression upstream in 2.7.0 on serializing & capturing exceptions
* **Data Classes(API Gateway)**: Add missing property `operationName` within request context
* **Misc.**: Numerous typing fixes to better to support MyPy across all utilities
* **Internal**: Downgraded poetry to 1.1.4 as there's been a regression with `importlib-metadata` in 1.1.5 not yet fixed

## 1.13.0 - 2021-03-23

### Added

* **Data Classes**: New S3 Object Lambda event

### Fixed

* **Docs**: Lambda Layer SAM template reference example

## 1.12.0 - 2021-03-17

### Added

* **Parameters**: New `force_fetch` param to always fetch the latest and bypass cache, if available
* **Data Classes**: New AppSync Lambda Resolver event covering both Direct Lambda Resolver and Amplify GraphQL Transformer Resolver `@function`
* **Data Classes**: New AppSync scalar utilities to easily compose Lambda Resolvers with date utils, uuid, etc.
* **Logger**: Support for Correlation ID both in `inject_lambda_context` decorator and `set_correlation_id` method
* **Logger**: Include new `exception_name` key to help customers easily enumerate exceptions across all functions

### Fixed

* **Tracer**: Type hint on return instance that made PyCharm no longer recognize autocompletion
* **Idempotency**: Error handling for missing idempotency key and `save_in_progress` errors

## 1.11.0 - 2021-03-05
### Fixed

* **Tracer**: Lazy loads X-Ray SDK to increase perf by 75% for those not instantiating Tracer
* **Metrics**: Optimize validation and serialization to increase perf by nearly 50% for large operations (<1ms)

### Added

* **Dataclass**: Add new Amazon Connect contact flow event
* **Idempotency**: New Idempotency utility
* **Docs**: Add example on how to integrate Batch utility with Sentry.io
* **Internal**: Added performance SLA tests for high level imports and Metrics validation/serialization

## 1.10.5 - 2021-02-17

No changes. Bumped version to trigger new pipeline build for layer publishing.

## 1.10.4 - 2021-02-17

### Fixed

* **Docs**: Fix anchor tags to be lower case
* **Docs**: Correct the docs location for the labeller

## 1.10.3 - 2021-02-04

### Added

* **Docs**: Migrated from Gatsby to MKdocs documentation system
* **Docs**: Included Getting started and Advanced sections in Core utilities, including additional examples

### Fixed

* **Tracer**: Disabled batching segments as X-Ray SDK does not flush traces upon reaching limits
* **Parser**: Model type is now compliant with mypy

## 1.10.2 - 2021-02-04

### Fixed

* **Utilities**: Correctly handle and list multiple exceptions in SQS batch processing utility.
* **Docs*:: Fix typos on AppConfig docstring import, and `SnsModel` typo in parser.
* **Utilities**: `typing_extensions` package is now only installed in Python < 3.8

## 1.10.1 - 2021-01-19

### Fixed

* **Utilities**: Added `SnsSqsEnvelope` in `parser` to dynamically adjust model mismatch when customers use SNS + SQS instead of SNS + Lambda, since we've discovered three payload keys are slightly different.

## 1.10.0 - 2021-01-18

### Added
- **Utilities**: Added support for AppConfig in Parameters utility
- **Logger**: Added support for `extra` parameter to add additional root fields when logging messages
- **Logger**: Added support to Pytest Live Log feat. via feature toggle `POWERTOOLS_LOG_DEDUPLICATION_DISABLED`
- **Tracer**: Added support to disable auto-capturing response and exception as metadata
- **Utilities**: Added support to handle custom string/integer formats in JSON Schema in Validator utility
- **Install**: Added new Lambda Layer with all extra dependencies installed, available in Serverless Application Repository (SAR)

### Fixed

- **Docs**: Added missing SNS parser model
- **Docs**: Added new environment variables for toggling features in Logger and Tracer: `POWERTOOLS_LOG_DEDUPLICATION_DISABLED`, `POWERTOOLS_TRACER_CAPTURE_RESPONSE`, `POWERTOOLS_TRACER_CAPTURE_ERROR`
- **Docs**: Fixed incorrect import for Cognito data classes in Event Sources utility

## 1.9.1 - 2020-12-21

### Fixed
- **Logger**: Bugfix to prevent parent loggers with the same name being configured more than once

### Added
- **Docs**: Add clarification to Tracer docs for how `capture_method` decorator can cause function responses to be read and serialized.
- **Utilities**: Added equality to ease testing Event source data classes
- **Package**: Added `py.typed` for initial work needed for PEP 561 compliance

## 1.9.0 - 2020-12-04

### Added
- **Utilities**: Added Kinesis, S3, CloudWatch Logs, Application Load Balancer, and SES support in `Parser`
- **Docs**: Sidebar menu are now always expanded

### Fixed
- **Docs**: Broken link to GitHub to homepage

## 1.8.0 - 2020-11-20

### Added
- **Utilities**: Added support for new EventBridge Replay field in `Parser` and `Event source data classes`
- **Utilities**: Added SNS support in `Parser`
- **Utilities**: Added API Gateway HTTP API data class support for new IAM and Lambda authorizer in `Event source data classes`
- **Docs**: Add new FAQ section for Logger on how to enable debug logging for boto3
- **Docs**: Add explicit minimal set of permissions required to use Layers provided by Serverless Application Repository (SAR)

### Fixed
- **Docs**: Fix typo in Dataclasses example for SES when fetching common email headers

## 1.7.0 - 2020-10-26

### Added
- **Utilities**: Add new `Parser` utility to provide parsing and deep data validation using Pydantic Models
- **Utilities**: Add case insensitive header lookup, and Cognito custom auth triggers to `Event source data classes`

### Fixed
- **Logger**: keeps Lambda root logger handler, and add log filter instead to prevent child log records duplication
- **Docs**: Improve wording on adding log keys conditionally

## 1.6.1 - 2020-09-23

### Fixed
- **Utilities**: Fix issue with boolean values in DynamoDB stream event data class.

## 1.6.0 - 2020-09-22

### Added
- **Metrics**: Support adding multiple metric values to a single metric name
- **Utilities**: Add new `Validator` utility to validate inbound events and responses using JSON Schema
- **Utilities**: Add new `Event source data classes` utility to easily describe event schema of popular event sources
- **Docs**: Add new `Testing your code` section to both Logger and Metrics page, and content width is now wider
- **Tracer**: Support for automatically disable Tracer when running a Chalice app

### Fixed
- **Docs**: Improve wording on log sampling feature in Logger, and removed duplicate content on main page
- **Utilities**: Remove DeleteMessageBatch API call when there are no messages to delete

## 1.5.0 - 2020-09-04

### Added
- **Logger**: Add `xray_trace_id` to log output to improve integration with CloudWatch Service Lens
- **Logger**: Allow reordering of logged output
- **Utilities**: Add new `SQS batch processing` utility to handle partial failures in processing message batches
- **Utilities**: Add typing utility providing static type for lambda context object
- **Utilities**: Add `transform=auto` in parameters utility to deserialize parameter values based on the key name

### Fixed
- **Logger**: The value of `json_default` formatter is no longer written to logs

## 1.4.0 - 2020-08-25

### Added
- **All**: Official Lambda Layer via [Serverless Application Repository](https://serverlessrepo.aws.amazon.com/applications/eu-west-1/057560766410/aws-lambda-powertools-python-layer)
- **Tracer**: `capture_method` and `capture_lambda_handler` now support **capture_response=False** parameter to prevent Tracer to capture response as metadata to allow customers running Tracer with sensitive workloads

### Fixed
- **Metrics**: Cold start metric is now completely separate from application metrics dimensions, making it easier and cheaper to visualize.
    - This is a breaking change if you were graphing/alerting on both application metrics with the same name to compensate this previous malfunctioning
    - Marked as bugfix as this is the intended behaviour since the beginning, as you shouldn't have the same application metric with different dimensions
- **Utilities**: SSMProvider within Parameters utility now have decrypt and recursive parameters correctly defined to support autocompletion

### Added
- **Tracer**: capture_lambda_handler and capture_method decorators now support `capture_response` parameter to not include function's response as part of tracing metadata

## 1.3.1 - 2020-08-22
### Fixed
- **Tracer**: capture_method decorator did not properly handle nested context managers

## 1.3.0 - 2020-08-21
### Added
- **Utilities**: Add new `parameters` utility to retrieve a single or multiple parameters from SSM Parameter Store, Secrets Manager, DynamoDB, or your very own

## 1.2.0 - 2020-08-20
### Added
- **Tracer**: capture_method decorator now supports generator functions (including context managers)

## 1.1.3 - 2020-08-18
### Fixed
- **Logger**: Logs emitted twice, structured and unstructured, due to Lambda configuring the root handler

## 1.1.2 - 2020-08-16
### Fixed
- **Docs**: Clarify confusion on Tracer reuse and `auto_patch=False` statement
- **Logger**: Autocomplete for log statements in PyCharm

## 1.1.1 - 2020-08-14
### Fixed
- **Logger**: Regression on `Logger` level not accepting `int` i.e. `Logger(level=logging.INFO)`

## 1.1.0 - 2020-08-14
### Added
- **Logger**: Support for logger inheritance with `child` parameter

### Fixed
- **Logger**: Log level is now case insensitive via params and env var

## 1.0.2 - 2020-07-16
### Fixed
- **Tracer**: Correct AWS X-Ray SDK dependency to support 2.5.0 and higher

## 1.0.1 - 2020-07-06
### Fixed
- **Logger**: Fix a bug with `inject_lambda_context` causing existing Logger keys to be overridden if `structure_logs` was called before

## 1.0.0 - 2020-06-18
### Added
- **Metrics**: `add_metadata` method to add any metric metadata you'd like to ease finding metric related data via CloudWatch Logs
- Set status as General Availability

## 0.11.0 - 2020-06-08
### Added
- Imports can now be made from top level of module, e.g.: `from aws_lambda_powertools import Logger, Metrics, Tracer`

### Fixed
- **Metrics**: Fix a bug with Metrics causing an exception to be thrown when logging metrics if dimensions were not explicitly added.

### Changed
- **Metrics**: No longer throws exception by default in case no metrics are emitted when using the log_metrics decorator.

## 0.10.0 - 2020-06-08
### Added
- **Metrics**: `capture_cold_start_metric` parameter added to `log_metrics` decorator
- **Metrics**: Optional `namespace` and `service` parameters added to Metrics constructor to more closely resemble other core utils

### Changed
- **Metrics**: Default dimension is now created based on `service` parameter or `POWERTOOLS_SERVICE_NAME` env var

### Deprecated
- **Metrics**: `add_namespace` method deprecated in favor of using `namespace` parameter to Metrics constructor or `POWERTOOLS_METRICS_NAMESPACE` env var

## 0.9.5 - 2020-06-02
### Fixed
- **Metrics**: Coerce non-string dimension values to string
- **Logger**: Correct `cold_start`, `function_memory_size` values from string to bool and int respectively

## 0.9.4 - 2020-05-29
### Fixed
- **Metrics**: Fix issue where metrics were not correctly flushed, and cleared on every invocation

## 0.9.3 - 2020-05-16
### Fixed
- **Tracer**: Fix Runtime Error for nested sync due to incorrect loop usage

## 0.9.2 - 2020-05-14
### Fixed
- **Tracer**: Import aiohttp lazily so it's not a hard dependency

## 0.9.0 - 2020-05-12
### Added
- **Tracer**: Support for async functions in `Tracer` via `capture_method` decorator
- **Tracer**: Support for `aiohttp` via `aiohttp_trace_config` trace config
- **Tracer**: Support for patching specific modules via `patch_modules` param
- **Tracer**: Document escape hatch mechanisms via `tracer.provider`

## 0.8.1 - 2020-05-1
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

## 0.8.0 - 2020-04-24
### Added
- **Logger**: Introduced `Logger` class for structured logging as a replacement for `logger_setup`
- **Logger**: Introduced `Logger.inject_lambda_context` decorator as a replacement for `logger_inject_lambda_context`

### Removed
- **Logger**: Raise `DeprecationWarning` exception for both `logger_setup`, `logger_inject_lambda_context`

## 0.7.0 - 2020-04-20
### Added
- **Middleware factory**: Introduced Middleware Factory to build your own middleware via `lambda_handler_decorator`

### Fixed
- **Metrics**: Fixed metrics dimensions not being included correctly in EMF

## 0.6.3 - 2020-04-09
### Fixed
- **Logger**: Fix `log_metrics` decorator logic not calling the decorated function, and exception handling

## 0.6.1 - 2020-04-08
### Added
- **Metrics**: Introduces Metrics middleware to utilise CloudWatch Embedded Metric Format

### Deprecated
- **Metrics**: Added deprecation warning for `log_metrics`

## 0.5.0 - 2020-02-20
### Added
- **Logger**: Introduced log sampling for debug - Thanks to [Danilo's contribution](https://github.com/awslabs/aws-lambda-powertools/pull/7)

## 0.1.0 - 2019-11-15
### Added
- Public beta release
