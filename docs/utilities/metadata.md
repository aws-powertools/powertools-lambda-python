---
title: Metadata
description: Utility
status: new
---

<!-- markdownlint-disable MD043 -->

The Metadata utility allows you to fetch data from the [AWS Lambda Metadata Endpoint (LMDS)](https://docs.aws.amazon.com/lambda/latest/dg/configuration-metadata-endpoint.html){target="_blank"}. This can be useful for retrieving information about the Lambda execution environment, such as the Availability Zone ID.

## Key features

* Fetch execution environment metadata from the Lambda Metadata Endpoint
* Automatic caching for the duration of the Lambda sandbox
* Graceful fallback to empty metadata outside Lambda (local dev, tests)
* Forward-compatible dataclass that can be extended as new fields are added

## Getting started

### Usage

You can fetch data from the Lambda Metadata Endpoint using the `get_lambda_metadata` function.

Import it from `aws_lambda_powertools.utilities.metadata` (the public package path):

```python
from aws_lambda_powertools.utilities.metadata import get_lambda_metadata
```

???+ warning "Import path is `utilities.metadata`"
    The correct module path is `aws_lambda_powertools.utilities.metadata`.

    Do **not** import from `aws_lambda_powertools.utilities.lambda_metadata` — that path is not part of the public API (even though the implementation file and `get_lambda_metadata` helper share a similar name).

???+ tip
    Metadata is cached for the duration of the Lambda sandbox, so subsequent calls to `get_lambda_metadata` will return the cached data.

=== "getting_started_metadata.py"

    ```python hl_lines="2 9 10"
    --8<-- "examples/metadata/src/getting_started_metadata.py"
    ```

You can also fetch metadata eagerly during cold start, so it's ready for subsequent invocations:

=== "getting_started_metadata_eager.py"

    ```python hl_lines="2 8"
    --8<-- "examples/metadata/src/getting_started_metadata_eager.py"
    ```

### Available metadata

| Property               | Type            | Description                                                    |
| ---------------------- | --------------- | -------------------------------------------------------------- |
| `availability_zone_id` | `str` or `None` | The AZ where the function is running (e.g., `use1-az1`)        |

## Testing your code

The metadata endpoint is not available during local development or testing. To ease testing, the `get_lambda_metadata` function automatically detects when it's running in a non-Lambda environment and returns an empty `LambdaMetadata` instance. This allows you to write tests without needing to mock the endpoint.

If you want to mock specific metadata values for testing purposes, you can patch the internal `_fetch_metadata` function and set the required environment variables:

=== "testing_metadata.py"

    ```python hl_lines="6-8 13-18 21"
    --8<-- "examples/metadata/src/testing_metadata.py"
    ```

We also expose a `clear_metadata_cache` function that can be used to clear the cached metadata, allowing you to test different metadata values within the same execution context.
