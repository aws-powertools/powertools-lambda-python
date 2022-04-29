---
title: Parameters
description: Utility
---


The parameters utility provides high-level functions to retrieve one or multiple parameter values from [AWS Systems Manager Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html){target="_blank"}, [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/){target="_blank"}, [AWS AppConfig](https://docs.aws.amazon.com/appconfig/latest/userguide/what-is-appconfig.html){target="_blank"}, [Amazon DynamoDB](https://aws.amazon.com/dynamodb/){target="_blank"}, or bring your own.

## Key features

* Retrieve one or multiple parameters from the underlying provider
* Cache parameter values for a given amount of time (defaults to 5 seconds)
* Transform parameter values from JSON or base 64 encoded strings
* Bring Your Own Parameter Store Provider

## Getting started

By default, we fetch parameters from System Manager Parameter Store, secrets from Secrets Manager, and application configuration from AppConfig.

### IAM Permissions

This utility requires additional permissions to work as expected.

???+ note
    Different parameter providers require different permissions.

Provider | Function/Method | IAM Permission
------------------------------------------------- | ------------------------------------------------- | ---------------------------------------------------------------------------------
SSM Parameter Store | `get_parameter`, `SSMProvider.get`  | `ssm:GetParameter`
SSM Parameter Store | `get_parameters`, `SSMProvider.get_multiple` | `ssm:GetParametersByPath`
Secrets Manager | `get_secret`, `SecretsManager.get` | `secretsmanager:GetSecretValue`
DynamoDB | `DynamoDBProvider.get` | `dynamodb:GetItem`
DynamoDB | `DynamoDBProvider.get_multiple` | `dynamodb:Query`
App Config | `AppConfigProvider.get_app_config`, `get_app_config` | `appconfig:GetConfiguration`

### Fetching parameters

You can retrieve a single parameter  using `get_parameter` high-level function.

For multiple parameters, you can use `get_parameters` and pass a path to retrieve them recursively.

```python hl_lines="1 6 10" title="Fetching multiple parameters recursively"
--8<-- "docs/examples/utilities/parameters/recursively_parameters.py"
```

### Fetching secrets

You can fetch secrets stored in Secrets Manager using `get_secrets`.

```python hl_lines="1 6" title="Fetching secrets"
--8<-- "docs/examples/utilities/parameters/fetching_secrets.py"
```

### Fetching app configurations

You can fetch application configurations in AWS AppConfig using `get_app_config`.

The following will retrieve the latest version and store it in the cache.

```python hl_lines="1 6-10" title="Fetching latest config from AppConfig"
--8<-- "docs/examples/utilities/parameters/fetching_app_config.py"
```

## Advanced

### Adjusting cache TTL

???+ tip
	`max_age` parameter is also available in high level functions like `get_parameter`, `get_secret`, etc.

By default, we cache parameters retrieved in-memory for 5 seconds.

You can adjust how long we should keep values in cache by using the param `max_age`, when using  `get()` or `get_multiple()` methods across all providers.

```python hl_lines="11 14" title="Caching parameter(s) value in memory for longer than 5 seconds"
--8<-- "docs/examples/utilities/parameters/custom_caching_parameters.py"
```

### Always fetching the latest

If you'd like to always ensure you fetch the latest parameter from the store regardless if already available in cache, use `force_fetch` param.

```python hl_lines="6" title="Forcefully fetching the latest parameter whether TTL has expired or not"
--8<-- "docs/examples/utilities/parameters/force_fetch_parameters.py"
```

### Built-in provider class

For greater flexibility such as configuring the underlying SDK client used by built-in providers, you can use their respective Provider Classes directly.

???+ tip
    This can be used to retrieve values from other regions, change the retry behavior, etc.

#### SSMProvider

```python hl_lines="6 11 14" title="Example with SSMProvider for further extensibility"
--8<-- "docs/examples/utilities/parameters/ssm_provider.py"
```

The AWS Systems Manager Parameter Store provider supports two additional arguments for the `get()` and `get_multiple()` methods:

| Parameter     | Default | Description |
|---------------|---------|-------------|
| **decrypt**   | `False` | Will automatically decrypt the parameter.
| **recursive** | `True`  | For `get_multiple()` only, will fetch all parameter values recursively based on a path prefix.

```python hl_lines="7 9" title="Example with get() and get_multiple()"
--8<-- "docs/examples/utilities/parameters/ssm_provider_get_options.py"
```

#### SecretsProvider

```python hl_lines="6 11" title="Example with SecretsProvider for further extensibility"
--8<-- "docs/examples/utilities/parameters/secrets_provider.py"
```

#### DynamoDBProvider

The DynamoDB Provider does not have any high-level functions, as it needs to know the name of the DynamoDB table containing the parameters.

**DynamoDB table structure for single parameters**

For single parameters, you must use `id` as the [partition key](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.CoreComponents.html#HowItWorks.CoreComponents.PrimaryKey) for that table.

???+ example

	DynamoDB table with `id` partition key and `value` as attribute

	| id         | value  |
	|--------------|----------|
	| my-parameter | my-value |

With this table, `dynamodb_provider.get("my-param")` will return `my-value`.

=== "app.py"

	```python hl_lines="3 8"
	--8<-- "docs/examples/utilities/parameters/dynamodb_provider.py"
	```

=== "DynamoDB Local example"
	You can initialize the DynamoDB provider pointing to [DynamoDB Local](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html) using `endpoint_url` parameter:

	```python hl_lines="5"
	--8<-- "docs/examples/utilities/parameters/dynamodb_provider_local.py"
	```

**DynamoDB table structure for multiple values parameters**

You can retrieve multiple parameters sharing the same `id` by having a sort key named `sk`.

???+ example

	DynamoDB table with `id` primary key, `sk` as sort key` and `value` as attribute

	| id        | sk    |   value  |
	|-------------|---------|------------|
	| my-hash-key | param-a | my-value-a |
	| my-hash-key | param-b | my-value-b |
	| my-hash-key | param-c | my-value-c |

With this table, `dynamodb_provider.get_multiple("my-hash-key")` will return a dictionary response in the shape of `sk:value`.

=== "app.py"

	```python hl_lines="3 9"
	--8<-- "docs/examples/utilities/parameters/dynamodb_provider_get_multiple.py"
	```

=== "parameters dict response"

	```json
	{
		"param-a": "my-value-a",
		"param-b": "my-value-b",
		"param-c": "my-value-c"
	}
	```

**Customizing DynamoDBProvider**

DynamoDB provider can be customized at initialization to match your table structure:

| Parameter      | Mandatory | Default | Description |
|----------------|-----------|---------|-------------|
| **table_name** | **Yes**   | *(N/A)* | Name of the DynamoDB table containing the parameter values.
| **key_attr**   | No        | `id`    | Hash key for the DynamoDB table.
| **sort_attr**  | No        | `sk`    | Range key for the DynamoDB table. You don't need to set this if you don't use the `get_multiple()` method.
| **value_attr** | No        | `value` | Name of the attribute containing the parameter value.

```python hl_lines="3-8" title="Customizing DynamoDBProvider to suit your table design"
--8<-- "docs/examples/utilities/parameters/dynamodb_provider_customization.py"
```

#### AppConfigProvider

```python hl_lines="6-10 15" title="Using AppConfigProvider"
--8<-- "docs/examples/utilities/parameters/app_config_provider.py"
```

### Create your own provider

You can create your own custom parameter store provider by inheriting the `BaseProvider` class, and implementing both `_get()` and `_get_multiple()` methods to retrieve a single, or multiple parameters from your custom store.

All transformation and caching logic is handled by the `get()` and `get_multiple()` methods from the base provider class.

Here is an example implementation using S3 as a custom parameter store:

```python hl_lines="6 9 20 30" title="Creating a S3 Provider to fetch parameters"
--8<-- "docs/examples/utilities/parameters/create_your_own_s3_provider.py"
```

### Deserializing values with transform parameter

For parameters stored in JSON or Base64 format, you can use the `transform` argument for deserialization.

???+ info
    The `transform` argument is available across all providers, including the high level functions.

=== "High level functions"

    ```python hl_lines="5"
	--8<-- "docs/examples/utilities/parameters/parameters_transform.py"
    ```

=== "Providers"

    ```python hl_lines="8 11"
	--8<-- "docs/examples/utilities/parameters/parameters_transform_providers.py"
    ```

#### Partial transform failures with `get_multiple()`

If you use `transform` with `get_multiple()`, you can have a single malformed parameter value. To prevent failing the entire request, the method will return a `None` value for the parameters that failed to transform.

You can override this by setting the `raise_on_transform_error` argument to `True`. If you do so, a single transform error will raise a **`TransformParameterError`** exception.

For example, if you have three parameters, */param/a*, */param/b* and */param/c*, but */param/c* is malformed:

```python hl_lines="11 17" title="Raising TransformParameterError at first malformed parameter"
--8<-- "docs/examples/utilities/parameters/parameters_transform_raise_on_transform_error.py"
```

#### Auto-transform values on suffix

If you use `transform` with `get_multiple()`, you might want to retrieve and transform parameters encoded in different formats.

You can do this with a single request by using `transform="auto"`. This will instruct any Parameter to to infer its type based on the suffix and transform it accordingly.

???+ info
    `transform="auto"` feature is available across all providers, including the high level functions.

```python hl_lines="7" title="Deserializing parameter values based on their suffix"
--8<-- "docs/examples/utilities/parameters/parameters_transform_auto.py"
```

For example, if you have two parameters with the following suffixes `.json` and `.binary`:

| Parameter name  | Parameter value      |
| --------------- | -------------------- |
| /param/a.json   | [some encoded value] |
| /param/a.binary | [some encoded value] |

The return of `ssm_provider.get_multiple("/param", transform="auto")` call will be a dictionary like:

```json
{
    "a.json": [some value],
    "b.binary": [some value]
}
```

### Passing additional SDK arguments

You can use arbitrary keyword arguments to pass it directly to the underlying SDK method.

```python hl_lines="7-8" title=""
--8<-- "docs/examples/utilities/parameters/parameters_sdk_args.py"
```

Here is the mapping between this utility's functions and methods and the underlying SDK:

| Provider            | Function/Method                 | Client name      | Function name |
|---------------------|---------------------------------|------------------|----------------|
| SSM Parameter Store | `get_parameter`                 | `ssm`            | [get_parameter](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.get_parameter) |
| SSM Parameter Store | `get_parameters`                | `ssm`            | [get_parameters_by_path](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.get_parameters_by_path) |
| SSM Parameter Store | `SSMProvider.get`               | `ssm`            | [get_parameter](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.get_parameter) |
| SSM Parameter Store | `SSMProvider.get_multiple`      | `ssm`            | [get_parameters_by_path](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.get_parameters_by_path) |
| Secrets Manager     | `get_secret`                    | `secretsmanager` | [get_secret_value](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/secretsmanager.html#SecretsManager.Client.get_secret_value) |
| Secrets Manager     | `SecretsManager.get`            | `secretsmanager` | [get_secret_value](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/secretsmanager.html#SecretsManager.Client.get_secret_value) |
| DynamoDB            | `DynamoDBProvider.get`          | `dynamodb`       | ([Table resource](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#table)) | [get_item](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#DynamoDB.Table.get_item)
| DynamoDB            | `DynamoDBProvider.get_multiple` | `dynamodb`       | ([Table resource](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#table)) | [query](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#DynamoDB.Table.query)
| App Config          | `get_app_config`                | `appconfig`      | [get_configuration](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/appconfig.html#AppConfig.Client.get_configuration) |

### Customizing boto configuration

The **`config`** and **`boto3_session`** parameters enable you to pass in a custom [botocore config object](https://botocore.amazonaws.com/v1/documentation/api/latest/reference/config.html) or a custom [boto3 session](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/core/session.html) when constructing any of the built-in provider classes.

???+ tip
	You can use a custom session for retrieving parameters cross-account/region and for snapshot testing.

=== "Custom session"

	```python hl_lines="1 5-6"
	--8<-- "docs/examples/utilities/parameters/parameters_custom_session.py"
	```
=== "Custom config"

	```python hl_lines="1 5-6"
	--8<-- "docs/examples/utilities/parameters/parameters_custom_config.py"
	```

## Testing your code

### Mocking parameter values

For unit testing your applications, you can mock the calls to the parameters utility to avoid calling AWS APIs. This can be achieved in a number of ways - in this example, we use the [pytest monkeypatch fixture](https://docs.pytest.org/en/latest/how-to/monkeypatch.html) to patch the `parameters.get_parameter` method:

=== "tests.py"

	```python
	--8<-- "docs/examples/utilities/parameters/testing_parameters_tests.py"
	```

=== "src/index.py"

	```python
	--8<-- "docs/examples/utilities/parameters/testing_parameters_index.py"
	```

If we need to use this pattern across multiple tests, we can avoid repetition by refactoring to use our own pytest fixture:

=== "tests.py"

	```python
	--8<-- "docs/examples/utilities/parameters/testing_parameters_fixture.py"
	```

Alternatively, if we need more fully featured mocking (for example checking the arguments passed to `get_parameter`), we
can use [unittest.mock](https://docs.python.org/3/library/unittest.mock.html) from the python stdlib instead of pytest's `monkeypatch` fixture. In this example, we use the
[patch](https://docs.python.org/3/library/unittest.mock.html#unittest.mock.patch) decorator to replace the `aws_lambda_powertools.utilities.parameters.get_parameter` function with a [MagicMock](https://docs.python.org/3/library/unittest.mock.html#unittest.mock.MagicMock)
object named `get_parameter_mock`.

=== "tests.py"
	```python
	--8<-- "docs/examples/utilities/parameters/testing_parameters_mock.py"
	```

### Clearing cache

Parameters utility caches all parameter values for performance and cost reasons. However, this can have unintended interference in tests using the same parameter name.

Within your tests, you can use `clear_cache` method available in [every provider](#built-in-provider-class). When using multiple providers or higher level functions like `get_parameter`, use `clear_caches` standalone function to clear cache globally.

=== "clear_cache method"
	```python hl_lines="8"
	--8<-- "docs/examples/utilities/parameters/testing_parameters_clear_cache.py"
	```

=== "global clear_caches"
	```python hl_lines="10"
	--8<-- "docs/examples/utilities/parameters/testing_parameters_global_clear_caches.py"
	```

=== "app.py"
	```python
	--8<-- "docs/examples/utilities/parameters/testing_parameters_app.py"
	```
