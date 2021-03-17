---
title: Parameters
description: Utility
---


The parameters utility provides high-level functions to retrieve one or multiple parameter values from [AWS Systems Manager Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html){target="_blank"}, [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/), [AWS AppConfig](https://aws.amazon.com/appconfig/){target="_blank"}, [Amazon DynamoDB](https://aws.amazon.com/dynamodb/){target="_blank"}, or bring your own.

## Key features

* Retrieve one or multiple parameters from the underlying provider
* Cache parameter values for a given amount of time (defaults to 5 seconds)
* Transform parameter values from JSON or base 64 encoded strings
* Bring Your Own Parameter Store Provider

## Getting started

By default, we fetch parameters from System Manager Parameter Store, secrets from Secrets Manager, and application configuration from AppConfig.

### IAM Permissions

This utility requires additional permissions to work as expected.

!!! note "Different parameter providers require different permissions"

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

=== "ssm_parameter_store.py"

    ```python hl_lines="1 5 9"
    from aws_lambda_powertools.utilities import parameters

    def handler(event, context):
        # Retrieve a single parameter
        value = parameters.get_parameter("/my/parameter")

        # Retrieve multiple parameters from a path prefix recursively
        # This returns a dict with the parameter name as key
        values = parameters.get_parameters("/my/path/prefix")
        for k, v in values.items():
            print(f"{k}: {v}")
    ```

### Fetching secrets

You can fetch secrets stored in Secrets Manager using `get_secrets`.

=== "secrets_manager.py"

    ```python hl_lines="1 5"
    from aws_lambda_powertools.utilities import parameters

    def handler(event, context):
        # Retrieve a single secret
        value = parameters.get_secret("my-secret")
    ```

### Fetching app configurations

> New in 1.10.0

You can fetch application configurations in AWS AppConfig using `get_app_config`.

The following will retrieve the latest version and store it in the cache.

=== "appconfig.py"

    ```python hl_lines="1 5"
    from aws_lambda_powertools.utilities import parameters

    def handler(event, context):
        # Retrieve a single configuration, latest version
        value: bytes = parameters.get_app_config(name="my_configuration", environment="my_env", application="my_app")
    ```

## Advanced

### Adjusting cache TTL

By default, we cache parameters retrieved in-memory for 5 seconds.

You can adjust how long we should keep values in cache by using the param `max_age`, when using  `get()` or `get_multiple()` methods across all providers.

=== "app.py"

    ```python hl_lines="9"
    from aws_lambda_powertools.utilities import parameters
    from botocore.config import Config

    config = Config(region_name="us-west-1")
    ssm_provider = parameters.SSMProvider(config=config)

    def handler(event, context):
        # Retrieve a single parameter
        value = ssm_provider.get("/my/parameter", max_age=60) # 1 minute

        # Retrieve multiple parameters from a path prefix
        values = ssm_provider.get_multiple("/my/path/prefix")
        for k, v in values.items():
            print(f"{k}: {v}")
    ```

### Always fetching the latest

If you'd like to always ensure you fetch the latest parameter from the store regardless if already available in cache, use `force_fetch` param.

=== "app.py"

    ```python hl_lines="5"
    from aws_lambda_powertools.utilities import parameters

    def handler(event, context):
        # Retrieve a single parameter
        value = parameters.get_parameter("/my/parameter", force_fetch=True)
    ```

### Built-in provider class

For greater flexibility such as configuring the underlying SDK client used by built-in providers, you can use their respective Provider Classes directly.

!!! tip "This can be used to retrieve values from other regions, change the retry behavior, etc."

#### SSMProvider

=== "ssm_parameter_store.py"

    ```python hl_lines="5 9 12"
    from aws_lambda_powertools.utilities import parameters
    from botocore.config import Config

    config = Config(region_name="us-west-1")
    ssm_provider = parameters.SSMProvider(config=config)

    def handler(event, context):
        # Retrieve a single parameter
        value = ssm_provider.get("/my/parameter")

        # Retrieve multiple parameters from a path prefix
        values = ssm_provider.get_multiple("/my/path/prefix")
        for k, v in values.items():
            print(f"{k}: {v}")
    ```

The AWS Systems Manager Parameter Store provider supports two additional arguments for the `get()` and `get_multiple()` methods:

| Parameter     | Default | Description |
|---------------|---------|-------------|
| **decrypt**   | `False` | Will automatically decrypt the parameter.
| **recursive** | `True`  | For `get_multiple()` only, will fetch all parameter values recursively based on a path prefix.

> **Example**

=== "ssm_parameter_store.py"

    ```python hl_lines="6 8"
    from aws_lambda_powertools.utilities import parameters

    ssm_provider = parameters.SSMProvider()

    def handler(event, context):
        decrypted_value = ssm_provider.get("/my/encrypted/parameter", decrypt=True)

        no_recursive_values = ssm_provider.get_multiple("/my/path/prefix", recursive=False)
    ```

#### SecretsProvider

=== "secrets_manager.py"

    ```python hl_lines="5 9"
    from aws_lambda_powertools.utilities import parameters
    from botocore.config import Config

    config = Config(region_name="us-west-1")
    secrets_provider = parameters.SecretsProvider(config=config)

    def handler(event, context):
        # Retrieve a single secret
        value = secrets_provider.get("my-secret")
    ```

#### DynamoDBProvider

The DynamoDB Provider does not have any high-level functions, as it needs to know the name of the DynamoDB table containing the parameters.

**DynamoDB table structure for single parameters**

For single parameters, you must use `id` as the [partition key](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.CoreComponents.html#HowItWorks.CoreComponents.PrimaryKey) for that table.

| id         | value  |
|--------------|----------|
| my-parameter | my-value |

> **Example**

=== "app.py"
	With this table, the return value of `dynamodb_provider.get("my-param")` call will be `my-value`.

    ```python hl_lines="3 7"
    from aws_lambda_powertools.utilities import parameters

    dynamodb_provider = parameters.DynamoDBProvider(table_name="my-table")

    def handler(event, context):
        # Retrieve a value from DynamoDB
        value = dynamodb_provider.get("my-parameter")
    ```

**DynamoDB table structure for multiple values parameters**

If you want to be able to retrieve multiple parameters at once sharing the same `id`, your table needs to contain a sort key name `sk`.

For example, if you want to retrieve multiple parameters having `my-hash-key` as ID:

| id        | sk    |   value  |
|-------------|---------|------------|
| my-hash-key | param-a | my-value-a |
| my-hash-key | param-b | my-value-b |
| my-hash-key | param-c | my-value-c |


With this table, the return of `dynamodb_provider.get_multiple("my-hash-key")` call will be a dictionary like:

```json
{
    "param-a": "my-value-a",
    "param-b": "my-value-b",
    "param-c": "my-value-c"
}
```

> **Example**

=== "app_multiple_parameters.py"

    ```python hl_lines="3 8"
    from aws_lambda_powertools.utilities import parameters

    dynamodb_provider = parameters.DynamoDBProvider(table_name="my-table")

    def handler(event, context):
        # Retrieve multiple values by performing a Query on the DynamoDB table
        # This returns a dict with the sort key attribute as dict key.
        values = dynamodb_provider.get_multiple("my-hash-key")
        for k, v in values.items():
            print(f"{k}: {v}")
    ```

**Additional arguments**

The DynamoDB provider supports four additional arguments at initialization. These can be used if you require a custom table structure:

| Parameter      | Mandatory | Default | Description |
|----------------|-----------|---------|-------------|
| **table_name** | **Yes**   | *(N/A)* | Name of the DynamoDB table containing the parameter values.
| **key_attr**   | No        | `id`    | Hash key for the DynamoDB table.
| **sort_attr**  | No        | `sk`    | Range key for the DynamoDB table. You don't need to set this if you don't use the `get_multiple()` method.
| **value_attr** | No        | `value` | Name of the attribute containing the parameter value.

> **Example**

=== "app.py"

    ```python hl_lines="3-8"
    from aws_lambda_powertools.utilities import parameters

    dynamodb_provider = parameters.DynamoDBProvider(
        table_name="my-table",
        key_attr="MyKeyAttr",
        sort_attr="MySortAttr",
        value_attr="MyvalueAttr"
    )

    def handler(event, context):
        value = dynamodb_provider.get("my-parameter")
    ```

#### AppConfigProvider

=== "app.py"

    ```python hl_lines="5 9"
    from aws_lambda_powertools.utilities import parameters
    from botocore.config import Config

    config = Config(region_name="us-west-1")
    appconf_provider = parameters.AppConfigProvider(environment="my_env", application="my_app", config=config)

    def handler(event, context):
        # Retrieve a single secret
        value: bytes = appconf_provider.get("my_conf")
    ```

### Create your own provider

You can create your own custom parameter store provider by inheriting the `BaseProvider` class, and implementing both `_get()` and `_get_multiple()` methods to retrieve a single, or multiple parameters from your custom store.

All transformation and caching logic is handled by the `get()` and `get_multiple()` methods from the base provider class.

Here is an example implementation using S3 as a custom parameter store:

=== "custom_provider.py"

    ```python hl_lines="3 6 17 27"
    import copy

    from aws_lambda_powertools.utilities import BaseProvider
    import boto3

    class S3Provider(BaseProvider):
        bucket_name = None
        client = None

        def __init__(self, bucket_name: str):
            # Initialize the client to your custom parameter store
            # E.g.:

            self.bucket_name = bucket_name
            self.client = boto3.client("s3")

        def _get(self, name: str, **sdk_options) -> str:
            # Retrieve a single value
            # E.g.:

            sdk_options["Bucket"] = self.bucket_name
            sdk_options["Key"] = name

            response = self.client.get_object(**sdk_options)
            return

        def _get_multiple(self, path: str, **sdk_options) -> Dict[str, str]:
            # Retrieve multiple values
            # E.g.:

            list_sdk_options = copy.deepcopy(sdk_options)

            list_sdk_options["Bucket"] = self.bucket_name
            list_sdk_options["Prefix"] = path

            list_response = self.client.list_objects_v2(**list_sdk_options)

            parameters = {}

            for obj in list_response.get("Contents", []):
                get_sdk_options = copy.deepcopy(sdk_options)

                get_sdk_options["Bucket"] = self.bucket_name
                get_sdk_options["Key"] = obj["Key"]

                get_response = self.client.get_object(**get_sdk_options)

                parameters[obj["Key"]] = get_response["Body"].read().decode()

            return parameters

    ```

### Deserializing values with transform parameter

For parameters stored in JSON or Base64 format, you can use the `transform` argument for deserialization.

!!! info "The `transform` argument is available across all providers, including the high level functions"

=== "High level functions"

    ```python hl_lines="4"
    from aws_lambda_powertools.utilities import parameters

    def handler(event, context):
        value_from_json = parameters.get_parameter("/my/json/parameter", transform="json")
    ```

=== "Providers"

    ```python hl_lines="7 10"
    from aws_lambda_powertools.utilities import parameters

    ssm_provider = parameters.SSMProvider()

    def handler(event, context):
        # Transform a JSON string
        value_from_json = ssm_provider.get("/my/json/parameter", transform="json")

        # Transform a Base64 encoded string
        value_from_binary = ssm_provider.get("/my/binary/parameter", transform="binary")
    ```

#### Partial transform failures with `get_multiple()`

If you use `transform` with `get_multiple()`, you can have a single malformed parameter value. To prevent failing the entire request, the method will return a `None` value for the parameters that failed to transform.

You can override this by setting the `raise_on_transform_error` argument to `True`. If you do so, a single transform error will raise a **`TransformParameterError`** exception.

For example, if you have three parameters, */param/a*, */param/b* and */param/c*, but */param/c* is malformed:

=== "partial_failures.py"

    ```python hl_lines="9 14-15"
    from aws_lambda_powertools.utilities import parameters

    ssm_provider = parameters.SSMProvider()

    def handler(event, context):
        # This will display:
        # /param/a: [some value]
        # /param/b: [some value]
        # /param/c: None
        values = ssm_provider.get_multiple("/param", transform="json")
        for k, v in values.items():
            print(f"{k}: {v}")

        # This will raise a TransformParameterError exception
        values = ssm_provider.get_multiple("/param", transform="json", raise_on_transform_error=True)
    ```

### Passing additional SDK arguments

You can use arbitrary keyword arguments to pass it directly to the underlying SDK method.

=== "ssm_parameter_store.py"

    ```python hl_lines="7"
    from aws_lambda_powertools.utilities import parameters

    secrets_provider = parameters.SecretsProvider()

    def handler(event, context):
        # The 'VersionId' argument will be passed to the underlying get_secret_value() call.
        value = secrets_provider.get("my-secret", VersionId="e62ec170-6b01-48c7-94f3-d7497851a8d2")
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
