---
title: Upgrade guide
description: Guide to update between major Powertools for AWS Lambda (Python) versions
---

<!-- markdownlint-disable MD043 -->

## Migrate to v3 from v2

!!! info "We strongly encourage you to migrate to v3. However, if you still need to upgrade from v1 to v2, you can find the [upgrade guide](/lambda/python/2.43.1/upgrade/)."

We've made minimal breaking changes to make your transition to v3 as smooth as possible.

### Quick summary

| Area                               | Change                                                                                                                   | Code change required |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------ | -------------------- |
| **Pydantic**                       | We have removed support for [Pydantic v1](#drop-support-for-pydantic-v1)                                                 | No                   |
| **Parser**                         | We have replaced [DynamoDBStreamModel](#dynamodbstreammodel-in-parser) `AttributeValue` with native Python types         | Yes                  |
| **Parser**                         | We no longer export [Pydantic objects](#importing-pydantic-objects) from `parser.pydantic`.                              | Yes                  |
| **Lambda layer**                   | [Lambda layers](#new-aws-lambda-layer-arns) are now compiled according to the specific Python version and architecture   | No                   |
| **Event Handler**                  | We [have deprecated](#event-handler-headers-are-case-insensitive) the `get_header_value` function.	                    | Yes                  |
| **Batch Processor**                | `@batch_processor` and `@async_batch_processor` decorators [are now deprecated](#deprecated-batch-processing-decorators) | Yes                  |
| **Event Source Data Classes**      | We have updated [default values](#event-source-default-values) for optional fields.                                      | Yes                  |
| **Parameters**                     | The [default cache TTL](#parameters-default-cache-ttl-updated-to-5-minutes) is now set to **5 minutes**                  | No                   |
| **Parameters**                     | The `config` parameter [is deprecated](#parameters-using-the-new-boto_config-parameter) in favor of `boto_config`        | Yes                  |
| **JMESPath Functions**             | The `extract_data_from_envelope` function is [deprecated in favor](#utilizing-the-new-query-function-in-jmespath-functions) of `query` | Yes    |
| **Types file**                     | We have removed the [type imports](#importing-types-from-typing-and-typing_annotations) from the `shared/types.py` file  | Yes                  |

### First Steps

Before you start, we suggest making a copy of your current working project or create a new branch with git.

1. **Upgrade** Python to at least v3.8.
2. **Ensure** you have the latest version via [Lambda Layer or PyPi](index.md#install){target="_blank"}.
3. **Review** the following sections to confirm if you need to make changes to your code.

## Drop support for Pydantic v1

!!! note "No code changes required"

As of June 30, 2024, Pydantic v1 has reached its end-of-life, and we have discontinued support for this version. We now exclusively support Pydantic v2.

Use [Pydantic v2 Migration Guide](https://docs.pydantic.dev/latest/migration/){target="_blank"} to migrate your custom Pydantic models to v2.

## DynamoDBStreamModel in parser

!!! info "This also applies if you're using [**DynamoDB BatchProcessor**](https://docs.powertools.aws.dev/lambda/python/latest/utilities/batch/#processing-messages-from-dynamodb){target="_blank"}."

`DynamoDBStreamModel` now returns native Python types when you access DynamoDB records through `Keys`, `NewImage`, and `OldImage` attributes.

Previously, you'd receive a raw JSON and need to deserialize each item to the type you'd want for convenience, or to the type DynamoDB stored via `get` method.

With this change, you can access data deserialized as stored in DynamoDB, and no longer need to recursively deserialize nested objects (Maps) if you had them.

???+ note
    For a lossless conversion of DynamoDB `Number` type, we follow AWS Python SDK (boto3) approach and convert to `Decimal`.

```diff
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

-        # BEFORE - v2
-        new_image: dict[str, Any] = record.dynamodb.NewImage
-        event_type = new_image["eventType"]["S"]
-        if event_type == "PENDING":
-            # deserialize attribute value into Python native type
-            # NOTE: nested objects would need additional logic
-            data = dict(new_image)
-            send_to_sqs(data)

+        # NOW - v3
+        new_image: dict[str, Any] = record.dynamodb.NewImage
+        if new_image.get("eventType") == "PENDING":
+            send_to_sqs(new_image)  # Here new_image is just a Python Dict type

```

## Importing Pydantic objects

We have stopped exporting Pydantic objects directly from `aws_lambda_powertools.utilities.parser.pydantic`. This change prevents customers from accidentally importing all of Pydantic, which could significantly slow down function startup times.

```diff
- #BEFORE - v2
- from aws_lambda_powertools.utilities.parser.pydantic import EmailStr

+ # NOW - v3
+ from pydantic import EmailStr
```

## New AWS Lambda Layer ARNs

!!! note "No code changes required"

To give you better a better experience, we're now building Powertools for AWS Lambda (Python)'s Lambda layers for specific Python versions (`3.8-3.12`) and architectures (`x86_64` & `arm64`).

This also allows us to include architecture-specific versions of both Pydantic v2 and AWS Encryption SDK and give you a more streamlined setup.

To take advantage of the new layers, you need to update your functions or deployment setup to include one of the new Lambda layer ARN from the table below:

| Architecture | Python version | Layer ARN                                                                                           |
| ------------ | -------------- | --------------------------------------------------------------------------------------------------- |
| x86_64       | 3.8            | arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python38-x86_64:{version}    |
| x86_64       | 3.9            | arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python39-x86_64:{version}    |
| x86_64       | 3.10           | arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python310-x86_64:{version}   |
| x86_64       | 3.11           | arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python311-x86_64:{version}   |
| x86_64       | 3.12           | arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python312-x86_64:{version}   |
| arm64        | 3.8            | arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python38-arm64:{version}     |
| arm64        | 3.9            | arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python39-arm64:{version}     |
| arm64        | 3.10           | arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python310-arm64:{version}    |
| arm64        | 3.11           | arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python311-arm64:{version}    |
| arm64        | 3.12           | arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-python312-arm64:{version}    |

## Event Handler: headers are case-insensitive

According to the [HTTP RFC](https://datatracker.ietf.org/doc/html/rfc9110#section-5.1){target="_blank"}, HTTP headers are case-insensitive. As a result, we have deprecated the `get_header_value` function to align with this standard. Instead, we recommend using `app.current_event.headers.get` to access header values directly

Consequently, the `case_sensitive` parameter in this function no longer has any effect, as we now ensure consistent casing by normalizing headers for you. This function will be removed in a future release, and we encourage users to adopt the new method to access header values.

```diff
import requests
from requests import Response

from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools.utilities.typing import LambdaContext

tracer = Tracer()
logger = Logger()
app = APIGatewayRestResolver()


@app.get("/todos")
@tracer.capture_method
def get_todos():
    endpoint = "https://jsonplaceholder.typicode.com/todos"

    # BEFORE - v2
-   api_key: str = app.current_event.get_header_value(name="X-Api-Key", case_sensitive=True, default_value="")

    # NOW - v3
+   api_key: str = app.current_event.headers.get("X-Api-Key", "")

    todos: Response = requests.get(endpoint, headers={"X-Api-Key": api_key})
    todos.raise_for_status()

    return {"todos": todos.json()}


# You can continue to use other utilities just as before
@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@tracer.capture_lambda_handler
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
```

## Deprecated Batch Processing decorators

In v2, we designated `@batch_processor` and `@async_batch_processor` as legacy modes for using the Batch Processing utility.

In v3, these have been marked as deprecated. Continuing to use them will result in warnings in your IDE and during Lambda execution.

```diff
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

-# BEFORE - v2
-@batch_processor(record_handler=record_handler, processor=processor)
-def lambda_handler(event, context: LambdaContext):
-    return processor.response()

+ # NOW - v3
+def lambda_handler(event, context: LambdaContext):
+ return process_partial_response(
+      event=event,
+      record_handler=record_handler,
+      processor=processor,
+      context=context,
+   )
```

## Event source default values

We've modified the **Event Source Data classes** so that optional dictionaries and lists now return empty strings, dictionaries or lists instead of `None`. This improvement simplifies your code by eliminating the need for conditional checks when accessing these fields, while maintaining backward compatibility with previous implementations.

We've applied this change broadly across various event source data classes, ensuring a more consistent and streamlined coding experience for you.

```diff
from aws_lambda_powertools.utilities.data_classes import DynamoDBStreamEvent, event_source
from aws_lambda_powertools.utilities.typing import LambdaContext


@event_source(data_class=DynamoDBStreamEvent)
def lambda_handler(event: DynamoDBStreamEvent, context: LambdaContext):
    for record in event.records:

-        # BEFORE - v2
-        old_image_type_return_v2 = type(record.dynamodb.old_image)
-        # Output is <class 'NoneType'>

+        # NOW - v3
+        old_image_type_return_v3 = type(record.dynamodb.old_image)
+        # Output is <class 'dict'>
```

## Parameters: default cache TTL updated to 5 minutes

!!! note "No code changes required"

We have updated the cache TTL from 5 seconds to 5 minutes to reduce the number of API calls to AWS, leading to improved performance and lower costs.

No code changes are necessary for this update; however, if you prefer the previous behavior, you can set the `max_age` parameter back to 5 seconds.

## Parameters: using the new boto_config parameter

In v2, you could use the `config` parameter to modify the **botocore Config** session settings.

In v3, we renamed this parameter to `boto_config` to standardize the name with other features, such as Idempotency, and introduced deprecation warnings for users still using `config`.

```diff
from botocore.config import Config

from aws_lambda_powertools.utilities import parameters

-# BEFORE - v2
-ssm_provider = parameters.SSMProvider(config=Config(region_name="us-west-1"))

+# NOW - v3
+ssm_provider = parameters.SSMProvider(boto_config=Config(region_name="us-west-1"))

def handler(event, context):
    value = ssm_provider.get("/my/parameter")
    return {"message": value}

```

## Utilizing the new query function in JMESPath Functions

In v2, you could use the `extract_data_from_envelope` function to search and extract data from dictionaries with JMESPath. This name was too generic and customers told us it was confusing.

In v3, we renamed this function to `query` to align with similar frameworks in the ecosystem, and introduced deprecation warnings for users still using `extract_data_from_envelope`.

```diff
from aws_lambda_powertools.utilities.jmespath_utils import extract_data_from_envelope, query
from aws_lambda_powertools.utilities.typing import LambdaContext


def handler(event: dict, context: LambdaContext) -> dict:
-   # BEFORE - v2
-   some_data = extract_data_from_envelope(data=event, envelope="powertools_json(body)")

+   # NOW - v3
+   some_data = query(data=event, envelope="powertools_json(body)")

    return {"data": some_data}
```

## Importing types from typing and typing_annotations

We refactored our codebase to align with Python guidelines and eliminated the use of `aws_lambda_powertools.shared.types` imports.

Instead, we now utilize types from the standard `typing` library, which are compatible with Python versions 3.8 and above, or from `typing_extensions` (included as a required dependency) for additional type support.

```diff
-# BEFORE - v2
-from aws_lambda_powertools.shared.types import Annotated

+# NOW - v3
+from typing_extensions import Annotated

from aws_lambda_powertools.utilities.typing import LambdaContext


def handler(event: dict, context: LambdaContext) -> dict:
    ...

```
