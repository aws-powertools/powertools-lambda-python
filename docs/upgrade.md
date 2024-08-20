---
title: Upgrade guide
description: Guide to update between major Powertools for AWS Lambda (Python) versions
---

<!-- markdownlint-disable MD043 -->

## Migrate to v3 from v2

We've made minimal breaking changes to make your transition to v3 as smooth as possible.

### Quick summary

| Area                               | Change                                                                                                                   | Code change required |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | -------------------- |
| **Pydantic**                       | Removed support for [Pydantic v1](#drop-support-for-pydantic-v1)                                                         | No                   |
| **Parser**                         | Replaced [DynamoDBStreamModel](#dynamodbstreammodel-in-parser) `AttributeValue` with native Python types                 | Yes                  |
| **Lambda layer**                   | [Lambda layers](#new-lambda-layers-arn) are now compiled according to the specific Python version and architecture       | No                   |
| **Batch Processor**                | `@batch_processor` and `@async_batch_processor` decorators [are now deprecated](#deprecated-batch-processing-decorators) | Yes                  |
| **Event Source Data Classes**      | New default values for optional fields                                                                                   | Yes                  |
| **Parameters**                     | The [default cache TTL](#parameters-default-cache-ttl-updated-to-5-minutes) is now set to **5 minutes**                                                                            | No                   |
| **Parameters**                     | The `config` parameter [is deprecated](#parameters-using-the-new-boto_config-parameter) in favor of `boto_config`                                                                   | Yes                   |
| **JMESPath Functions**             | The `extract_data_from_envelope` function is [deprecated in favor](#utilizing-the-new-query-function-in-jmespath-functions) of `query` | Yes                   |
| **Types file**                     | We have removed the [type imports](#importing-types-from-typing-and-typing_annotations) from the `shared/types.py` file                                                        | Yes                  |

### First Steps

Before you start, we suggest making a copy of your current working project or create a new branch with git.

1. **Upgrade** Python to at least v3.8
2. **Ensure** you have the latest version via [Lambda Layer or PyPi](index.md#install){target="_blank"}.
3. **Review** the following sections to confirm whether they affect your code

## Drop support for Pydantic v1

!!! note "No code changes required"

As of June 30, 2024, Pydantic v1 has reached its end-of-life, and we have discontinued support for this version. We now exclusively support Pydantic v2.

You don't need to make any changes related to Powertools for AWS Lambda (Python) on your end.

## DynamoDBStreamModel in parser

!!! info "This also applies if you're using [**DynamoDB BatchProcessor**](https://docs.powertools.aws.dev/lambda/python/latest/utilities/batch/#processing-messages-from-dynamodb){target="_blank"}."

You will now receive native Python types when accessing DynamoDB records via `Keys`, `NewImage`, and `OldImage` attributes in `DynamoDBStreamModel`.

Previously, you'd receive a raw JSON and need to deserialize each item to the type you'd want for convenience, or to the type DynamoDB stored via `get` method.

With this change, you can access data deserialized as stored in DynamoDB, and no longer need to recursively deserialize nested objects (Maps) if you had them.

???+ note
    For a lossless conversion of DynamoDB `Number` type, we follow AWS Python SDK (boto3) approach and convert to `Decimal`.

```python hl_lines="21-27 30-31"
from __future__ import annotations

import json
from typing import Any

from aws_lambda_powertools.utilities.parser import event_parser
from aws_lambda_powertools.utilities.parser.models import DynamoDBStreamModel
from aws_lambda_powertools.utilities.typing import LambdaContext


def send_to_sqs(data: dict):
    body = json.dumps(data)
    ...

@event_parser
def lambda_handler(event: DynamoDBStreamModel, context: LambdaContext):

    for record in event.Records:

        # BEFORE - V2
        new_image: dict[str, Any] = record.dynamodb.NewImage
        event_type = new_image["eventType"]["S"]
        if event_type == "PENDING":
            # deserialize attribute value into Python native type
            # NOTE: nested objects would need additional logic
            data = dict(new_image)
            send_to_sqs(data)

        # NOW - V3
        new_image: dict[str, Any] = record.dynamodb.NewImage
        if new_image.get("eventType") == "PENDING":
            send_to_sqs(new_image)  # Here new_image is just a Python Dict type

```

## New Lambda layers ARN

!!! note "No code changes required"

Our Lambda layers are now compiled according to the specific Python version and architecture, resulting in a change to the ARN.

You need to update your deployment to include this new ARN and use the V3. Additionally, we are now including Pydantic v2 and the AWS Encryption SDK in our Lambda layers.

Check the new formats:

| Layer ARN                                                                                        | Python version  | Architecture |
| ------------------------------------------------------------------------------------------------ | --------------- | ------------ |
| arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python38-x86:{version}    | 3.8             | x86_64       |
| arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python39-x86:{version}    | 3.9             | x86_64       |
| arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python310-x86:{version}   | 3.10            | x86_64       |
| arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python311-x86:{version}   | 3.11            | x86_64       |
| arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python312-x86:{version}   | 3.12            | x86_64       |
| arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python38-arm64:{version}  | 3.8             | arm64        |
| arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python39-arm64:{version}  | 3.9             | arm64        |
| arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python310-arm64:{version} | 3.10            | arm64        |
| arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python311-arm64:{version} | 3.11            | arm64        |
| arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python312-arm64:{version} | 3.12            | arm64        |

## Deprecated Batch Processing decorators

In V2, we designated `@batch_processor` and `@async_batch_processor` as legacy modes for using the Batch Processing utility.

In V3, these have been marked as deprecated. Continuing to use them will result in warnings in your IDE and during Lambda execution.

```python hl_lines="17-19 22-28"
import json

from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, batch_processor, process_partial_response
from aws_lambda_powertools.utilities.data_classes.sqs_event import SQSRecord
from aws_lambda_powertools.utilities.typing import LambdaContext

processor = BatchProcessor(event_type=EventType.SQS)

@tracer.capture_method
def record_handler(record: SQSRecord):
    payload: str = record.body
    if payload:
        item: dict = json.loads(payload)
        logger.info(item)

# BEFORE - V2
@batch_processor(record_handler=record_handler, processor=processor)
def lambda_handler(event, context: LambdaContext):
    return processor.response()

# NOW - V3
def lambda_handler(event, context: LambdaContext):
    return process_partial_response(
        event=event,
        record_handler=record_handler,
        processor=processor,
        context=context,
    )
```

## Parameters: default cache TTL updated to 5 minutes

!!! note "No code changes required"

We have updated the cache TTL to 5 minutes to reduce the number of API calls to AWS, leading to improved performance and lower costs.

No code changes are necessary for this update; however, if you prefer the previous 5-second TTL, you can easily revert to that setting by utilizing the `max_age` parameter.

## Parameters: using the new boto_config parameter

 In V2, you could use the `config` parameter to modify the **botocore Config** session settings.

 In V3, we renamed this parameter to `boto_config` and introduced deprecation warnings for users still utilizing `config`.

```python hl_lines="5 6 8 9"
from botocore.config import Config

from aws_lambda_powertools.utilities import parameters

# BEFORE - V2
ssm_provider = parameters.SSMProvider(config=Config(region_name="us-west-1"))

# NOW - V3
ssm_provider = parameters.SSMProvider(boto_config=Config(region_name="us-west-1"))

def handler(event, context):
    value = ssm_provider.get("/my/parameter")
    return {"message": value}

```

## Utilizing the new query function in JMESPath Functions

In V2, you could use the `extract_data_from_envelope` function to search and extract data from dictionaries with JMESPath.

In V3, we renamed this function to `query` and introduced deprecation warnings for users still utilizing `extract_data_from_envelope`.

```python hl_lines="6-7 9-10"
from aws_lambda_powertools.utilities.jmespath_utils import extract_data_from_envelope, query
from aws_lambda_powertools.utilities.typing import LambdaContext


def handler(event: dict, context: LambdaContext) -> dict:
    # BEFORE - V2
    some_data = extract_data_from_envelope(data=event, envelope="powertools_json(body)")

    # NOW - V3
    some_data = query(data=event, envelope="powertools_json(body)")

    return {"data": some_data}
```

## Importing types from typing and typing_annotations

We refactored our codebase to align with some PEP style guidelines and eliminated the use of `aws_lambda_powertools.shared.types` imports. Instead, we now utilize types from the standard `typing` library, which are compatible with Python versions 3.8 and above, or from `typing_extensions` for additional type support.

Since V2, we have included `typing_extensions` as a dependency. If you require additional types is not supported by a specific Python version, you can import them from `typing_extensions`.

```python hl_lines="1 2 4 5"
# BEFORE - V2
from aws_lambda_powertools.shared.types import Annotated

# NOW - V3
from typing_extensions import Annotated

from aws_lambda_powertools.utilities.typing import LambdaContext


def handler(event: dict, context: LambdaContext) -> dict:
    ...

```
