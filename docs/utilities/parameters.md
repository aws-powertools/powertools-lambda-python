---
title: Parameters
description: Utility
---

<!-- markdownlint-disable MD013 -->
The parameters utility provides high-level functions to retrieve one or multiple parameter values from [AWS Systems Manager Parameter Store](https://docs.aws.amazon.com/systems-manager/latest/userguide/systems-manager-parameter-store.html){target="_blank"}, [AWS Secrets Manager](https://aws.amazon.com/secrets-manager/){target="_blank"}, [AWS AppConfig](https://docs.aws.amazon.com/appconfig/latest/userguide/what-is-appconfig.html){target="_blank"}, [Amazon DynamoDB](https://aws.amazon.com/dynamodb/){target="_blank"}, or bring your own.

## Key features

* Retrieve one or multiple parameters from the underlying provider
* Cache parameter values for a given amount of time (defaults to 5 seconds)
* Transform parameter values from JSON or base 64 encoded strings
* Bring Your Own Parameter Store Provider

## Getting started

???+ tip
    All examples shared in this documentation are available within the [project repository](https://github.com/aws-powertools/powertools-lambda-python/tree/develop/examples){target="_blank"}.

By default, we fetch parameters from System Manager Parameter Store, secrets from Secrets Manager, and application configuration from AppConfig.

### IAM Permissions

This utility requires additional permissions to work as expected.

???+ note
    Different parameter providers require different permissions.

| Provider  | Function/Method                                                        | IAM Permission                                                                       |
| --------- | ---------------------------------------------------------------------- | ------------------------------------------------------------------------------------ |
| SSM       | **`get_parameter`**, **`SSMProvider.get`**                             | **`ssm:GetParameter`**                                                               |
| SSM       | **`get_parameters`**, **`SSMProvider.get_multiple`**                   | **`ssm:GetParametersByPath`**                                                        |
| SSM       | **`get_parameters_by_name`**, **`SSMProvider.get_parameters_by_name`** | **`ssm:GetParameter`** and **`ssm:GetParameters`**                                   |
| SSM       | If using **`decrypt=True`**                                            | You must add an additional permission **`kms:Decrypt`**                              |
| Secrets   | **`get_secret`**, **`SecretsProvider.get`**                            | **`secretsmanager:GetSecretValue`**                                                 |
| DynamoDB  | **`DynamoDBProvider.get`**                                             | **`dynamodb:GetItem`**                                                               |
| DynamoDB  | **`DynamoDBProvider.get_multiple`**                                    | **`dynamodb:Query`**                                                                 |
| AppConfig | **`get_app_config`**, **`AppConfigProvider.get_app_config`**           | **`appconfig:GetLatestConfiguration`** and **`appconfig:StartConfigurationSession`** |

### Fetching parameters

You can retrieve a single parameter using the `get_parameter` high-level function.

=== "getting_started_single_ssm_parameter.py"
    ```python hl_lines="3 10"
    --8<-- "examples/parameters/src/getting_started_single_ssm_parameter.py"
    ```

For multiple parameters, you can use either:

* `get_parameters` to recursively fetch all parameters by path.
* `get_parameters_by_name` to fetch distinct parameters by their full name. It also accepts custom caching, transform, decrypt per parameter.

=== "getting_started_recursive_ssm_parameter.py"
    ```python hl_lines="3 10 13"
    --8<-- "examples/parameters/src/getting_started_recursive_ssm_parameter.py"
    ```

=== "getting_started_parameter_by_name.py"
    ```python hl_lines="3 14"
    --8<-- "examples/parameters/src/getting_started_parameter_by_name.py"
    ```

???+ tip "`get_parameters_by_name` supports graceful error handling"
	By default, we will raise `GetParameterError` when any parameter fails to be fetched. You can override it by setting `raise_on_error=False`.

	When disabled, we take the following actions:

	* Add failed parameter name in the `_errors` key, _e.g._, `{_errors: ["/param1", "/param2"]}`
	* Keep only successful parameter names and their values in the response
	* Raise `GetParameterError` if any of your parameters is named `_errors`

=== "get_parameter_by_name_error_handling.py"
    ```python hl_lines="3 5 12-13 15"
    --8<-- "examples/parameters/src/get_parameter_by_name_error_handling.py"
    ```

### Fetching secrets

You can fetch secrets stored in Secrets Manager using `get_secret`.

=== "getting_started_secret.py"
    ```python hl_lines="5 15"
    --8<-- "examples/parameters/src/getting_started_secret.py"
    ```

### Fetching app configurations

You can fetch application configurations in AWS AppConfig using `get_app_config`.

The following will retrieve the latest version and store it in the cache.

???+ warning
	We make two API calls to fetch each unique configuration name during the first time. This is by design in AppConfig. Please consider adjusting `max_age` parameter to enhance performance.

=== "getting_started_appconfig.py"
    ```python hl_lines="5 12"
    --8<-- "examples/parameters/src/getting_started_appconfig.py"
    ```

## Advanced

### Adjusting cache TTL

???+ tip
	`max_age` parameter is also available in underlying provider functions like `get()`, `get_multiple()`, etc.

By default, we cache parameters retrieved in-memory for 5 seconds. If you want to change this default value and set the same TTL for all parameters, you can set the `POWERTOOLS_PARAMETERS_MAX_AGE` environment variable. **You can still set `max_age` for individual parameters**.

You can adjust how long we should keep values in cache by using the param `max_age`, when using  `get_parameter()`, `get_parameters()` and `get_secret()` methods across all providers.

=== "single_ssm_parameter_with_cache.py"
    ```python hl_lines="5 12"
    --8<-- "examples/parameters/src/single_ssm_parameter_with_cache.py"
    ```

=== "recursive_ssm_parameter_with_cache.py"
    ```python hl_lines="5 12"
    --8<-- "examples/parameters/src/recursive_ssm_parameter_with_cache.py"
    ```

=== "secret_with_cache.py"
    ```python hl_lines="5 15"
    --8<-- "examples/parameters/src/secret_with_cache.py"
    ```

=== "appconfig_with_cache.py"
    ```python hl_lines="5 12-14"
    --8<-- "examples/parameters/src/appconfig_with_cache.py"
    ```

### Always fetching the latest

If you'd like to always ensure you fetch the latest parameter from the store regardless if already available in cache, use `force_fetch` param.

=== "single_ssm_parameter_force_fetch.py"
    ```python hl_lines="5 12"
    --8<-- "examples/parameters/src/single_ssm_parameter_force_fetch.py"
    ```

=== "recursive_ssm_parameter_force_fetch.py"
    ```python hl_lines="5 12"
    --8<-- "examples/parameters/src/recursive_ssm_parameter_force_fetch.py"
    ```

=== "secret_force_fetch.py"
    ```python hl_lines="5 15"
    --8<-- "examples/parameters/src/secret_force_fetch.py"
    ```

=== "appconfig_force_fetch.py"
    ```python hl_lines="5 12-14"
    --8<-- "examples/parameters/src/appconfig_force_fetch.py"
    ```

### Built-in provider class

For greater flexibility such as configuring the underlying SDK client used by built-in providers, you can use their respective Provider Classes directly.

???+ tip
    This is useful when you need to customize parameters for the SDK client, such as region, credentials, retries and others. For more information, read [botocore.config](https://botocore.amazonaws.com/v1/documentation/api/latest/reference/config.html) and [boto3.session](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/core/session.html#module-boto3.session).

#### SSMProvider

=== "builtin_provider_ssm_single_parameter.py"
    ```python hl_lines="6 11 12"
    --8<-- "examples/parameters/src/builtin_provider_ssm_single_parameter.py"
    ```

=== "builtin_provider_ssm_recursive_parameter.py"
    ```python hl_lines="6 19-25"
    --8<-- "examples/parameters/src/builtin_provider_ssm_recursive_parameter.py"
    ```

The AWS Systems Manager Parameter Store provider supports two additional arguments for the `get()` and `get_multiple()` methods:

| Parameter     | Default | Description                                                                                    |
| ------------- | ------- | ---------------------------------------------------------------------------------------------- |
| **decrypt**   | `False` | Will automatically decrypt the parameter.                                                      |
| **recursive** | `True`  | For `get_multiple()` only, will fetch all parameter values recursively based on a path prefix. |

You can create `SecureString` parameters, which are parameters that have a plaintext parameter name and an encrypted parameter value. If you don't use the `decrypt` argument, you will get an encrypted value. Read [here](https://docs.aws.amazon.com/kms/latest/developerguide/services-parameter-store.html) about best practices using KMS to secure your parameters.

???+ tip
	If you want to always decrypt parameters, you can set the `POWERTOOLS_PARAMETERS_SSM_DECRYPT=true` environment variable. **This will override the default value of `false` but you can still set the `decrypt` option for individual parameters**.

=== "builtin_provider_ssm_with_decrypt.py"
    ```python hl_lines="6 10 16"
    --8<-- "examples/parameters/src/builtin_provider_ssm_with_decrypt.py"
    ```

=== "builtin_provider_ssm_with_no_recursive.py"
    ```python hl_lines="5 8 21"
    --8<-- "examples/parameters/src/builtin_provider_ssm_with_no_recursive.py"
    ```

#### SecretsProvider

=== "builtin_provider_secret.py"
    ```python hl_lines="4 6 9"
    --8<-- "examples/parameters/src/builtin_provider_secret.py"
    ```

#### DynamoDBProvider

The DynamoDB Provider does not have any high-level functions, as it needs to know the name of the DynamoDB table containing the parameters.

**DynamoDB table structure for single parameters**

For single parameters, you must use `id` as the [partition key](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/HowItWorks.CoreComponents.html#HowItWorks.CoreComponents.PrimaryKey) for that table.

???+ example

	DynamoDB table with `id` partition key and `value` as attribute

 | id           | value    |
 | ------------ | -------- |
 | my-parameter | my-value |

With this table, `dynamodb_provider.get("my-parameter")` will return `my-value`.

=== "builtin_provider_dynamodb_single_parameter.py"
    ```python hl_lines="5 8 15"
    --8<-- "examples/parameters/src/builtin_provider_dynamodb_single_parameter.py"
    ```

=== "sam_dynamodb_table_single.yaml"
    ```yaml hl_lines="12-14"
    --8<-- "examples/parameters/sam/sam_dynamodb_table_single.yaml"
    ```

You can initialize the DynamoDB provider pointing to [DynamoDB Local](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/DynamoDBLocal.html) using `endpoint_url` parameter:

=== "builtin_provider_dynamodb_custom_endpoint.py"
    ```python hl_lines="5 8 15"
    --8<-- "examples/parameters/src/builtin_provider_dynamodb_custom_endpoint.py"
    ```

**DynamoDB table structure for multiple values parameters**

You can retrieve multiple parameters sharing the same `id` by having a sort key named `sk`.

???+ example

	DynamoDB table with `id` primary key, `sk` as sort key and `value` as attribute

 | id     | sk                | value                                            |
 | ------ | ----------------- | ------------------------------------------------ |
 | config | endpoint_comments | <https://jsonplaceholder.typicode.com/comments/> |
 | config | limit             | 10                                               |

With this table, `dynamodb_provider.get_multiple("config")` will return a dictionary response in the shape of `sk:value`.

=== "builtin_provider_dynamodb_recursive_parameter.py"
    ```python hl_lines="5 8 15"
    --8<-- "examples/parameters/src/builtin_provider_dynamodb_recursive_parameter.py"
    ```

=== "sam_dynamodb_table_recursive.yaml"
    ```yaml hl_lines="15-18"
    --8<-- "examples/parameters/sam/sam_dynamodb_table_recursive.yaml"
    ```

**Customizing DynamoDBProvider**

DynamoDB provider can be customized at initialization to match your table structure:

| Parameter      | Mandatory | Default | Description                                                                                                |
| -------------- | --------- | ------- | ---------------------------------------------------------------------------------------------------------- |
| **table_name** | **Yes**   | *(N/A)* | Name of the DynamoDB table containing the parameter values.                                                |
| **key_attr**   | No        | `id`    | Hash key for the DynamoDB table.                                                                           |
| **sort_attr**  | No        | `sk`    | Range key for the DynamoDB table. You don't need to set this if you don't use the `get_multiple()` method. |
| **value_attr** | No        | `value` | Name of the attribute containing the parameter value.                                                      |

=== "builtin_provider_dynamodb_custom_fields.py"
    ```python hl_lines="3 8-10 17"
    --8<-- "examples/parameters/src/builtin_provider_dynamodb_custom_fields.py"
    ```

=== "sam_dynamodb_custom_fields.yaml"
    ```yaml hl_lines="5 8-10 17"
    --8<-- "examples/parameters/sam/sam_dynamodb_custom_fields.yaml"
    ```

#### AppConfigProvider

=== "builtin_provider_appconfig.py"
    ```python hl_lines="6 9 10 16"
    --8<-- "examples/parameters/src/builtin_provider_appconfig.py"
    ```

### Create your own provider

You can create your own custom parameter store provider by inheriting the `BaseProvider` class, and implementing both `_get()` and `_get_multiple()` methods to retrieve a single, or multiple parameters from your custom store.

All transformation and caching logic is handled by the `get()` and `get_multiple()` methods from the base provider class.

Here are two examples of implementing a custom parameter store. One using an external service like [Hashicorp Vault](https://www.vaultproject.io/){target="_blank"}, a widely popular key-value and secret storage and the other one using [Amazon S3](https://aws.amazon.com/s3/?nc1=h_ls){target="_blank"}, a popular object storage.

=== "working_with_own_provider_vault.py"
    ```python hl_lines="5 13 20 24"
    --8<-- "examples/parameters/src/working_with_own_provider_vault.py"
    ```

=== "custom_provider_vault.py"
    ```python hl_lines="6 9 17 24"
    --8<-- "examples/parameters/src/custom_provider_vault.py"
    ```

=== "working_with_own_provider_s3.py"
    ```python hl_lines="4 11 18 21"
    --8<-- "examples/parameters/src/working_with_own_provider_s3.py"
    ```

=== "custom_provider_s3.py"
    ```python hl_lines="6 9 19 29"
    --8<-- "examples/parameters/src/custom_provider_s3.py"
    ```

### Deserializing values with transform parameter

For parameters stored in JSON or Base64 format, you can use the `transform` argument for deserialization.

???+ info
    The `transform` argument is available across all providers, including the high level functions.

=== "working_with_transform_high_level.py"
    ```python hl_lines="5 12"
    --8<-- "examples/parameters/src/working_with_transform_high_level.py"
    ```

=== "working_with_transform_provider.py"
    ```python hl_lines="6 9 16"
    --8<-- "examples/parameters/src/working_with_transform_provider.py"
    ```

#### Partial transform failures with `get_multiple()`

If you use `transform` with `get_multiple()`, you can have a single malformed parameter value. To prevent failing the entire request, the method will return a `None` value for the parameters that failed to transform.

You can override this by setting the `raise_on_transform_error` argument to `True`. If you do so, a single transform error will raise a **`TransformParameterError`** exception.

For example, if you have three parameters, */param/a*, */param/b* and */param/c*, but */param/c* is malformed:

=== "handling_error_transform.py"
    ```python hl_lines="3 14 20"
    --8<-- "examples/parameters/src/handling_error_transform.py"
    ```

#### Auto-transform values on suffix

If you use `transform` with `get_multiple()`, you might want to retrieve and transform parameters encoded in different formats.

You can do this with a single request by using `transform="auto"`. This will instruct any Parameter to to infer its type based on the suffix and transform it accordingly.

???+ info
    `transform="auto"` feature is available across all providers, including the high level functions.

=== "working_with_auto_transform.py"
    ```python hl_lines="1 4 8"
    --8<-- "examples/parameters/src/working_with_auto_transform.py"
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

=== "working_with_sdk_additional_arguments.py"
    ```python hl_lines="1 4 9"
    --8<-- "examples/parameters/src/working_with_sdk_additional_arguments.py"
    ```

Here is the mapping between this utility's functions and methods and the underlying SDK:

| Provider            | Function/Method                 | Client name      | Function name                                                                                                                                                                                                                                                                                                                                             |
| ------------------- | ------------------------------- | ---------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| SSM Parameter Store | `get_parameter`                 | `ssm`            | [get_parameter](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.get_parameter){target="_blank"}                                                                                                                                                                                                                             |
| SSM Parameter Store | `get_parameters`                | `ssm`            | [get_parameters_by_path](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.get_parameters_by_path){target="_blank"}                                                                                                                                                                                                           |
| SSM Parameter Store | `SSMProvider.get`               | `ssm`            | [get_parameter](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.get_parameter){target="_blank"}                                                                                                                                                                                                                             |
| SSM Parameter Store | `SSMProvider.get_multiple`      | `ssm`            | [get_parameters_by_path](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/ssm.html#SSM.Client.get_parameters_by_path){target="_blank"}                                                                                                                                                                                                           |
| Secrets Manager     | `get_secret`                    | `secretsmanager` | [get_secret_value](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/secretsmanager.html#SecretsManager.Client.get_secret_value){target="_blank"}                                                                                                                                                                                                 |
| Secrets Manager     | `SecretsProvider.get`            | `secretsmanager` | [get_secret_value](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/secretsmanager.html#SecretsManager.Client.get_secret_value){target="_blank"}                                                                                                                                                                                                 |
| DynamoDB            | `DynamoDBProvider.get`          | `dynamodb`       | ([Table resource](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#table){target="_blank"})                                                                                                                                                                                                                                        | [get_item](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#DynamoDB.Table.get_item) |
| DynamoDB            | `DynamoDBProvider.get_multiple` | `dynamodb`       | ([Table resource](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#table){target="_blank"})                                                                                                                                                                                                                                        | [query](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html#DynamoDB.Table.query)       |
| App Config          | `get_app_config`                | `appconfigdata`  | [start_configuration_session](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/appconfigdata.html#AppConfigData.Client.start_configuration_session){target="_blank"} and [get_latest_configuration](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/appconfigdata.html#AppConfigData.Client.get_latest_configuration){target="_blank"} |

### Bring your own boto client

You can use `boto3_client` parameter via any of the available [Provider Classes](#built-in-provider-class). Some providers expect a low level boto3 client while others expect a high level boto3 client, here is the mapping for each of them:

| Provider                                | Type       | Boto client construction        |
| --------------------------------------- | ---------- | ------------------------------- |
| [SSMProvider](#ssmprovider)             | low level  | `boto3.client("ssm")`           |
| [SecretsProvider](#secretsprovider)     | low level  | `boto3.client("secrets")`       |
| [AppConfigProvider](#appconfigprovider) | low level  | `boto3.client("appconfigdata")` |
| [DynamoDBProvider](#dynamodbprovider)   | high level | `boto3.resource("dynamodb")`    |

Bringing them together in a single code snippet would look like this:

=== "custom_boto3_all_providers.py"
    ```python hl_lines="4 6"
    --8<-- "examples/parameters/src/custom_boto3_all_providers.py"
    ```

???+ question "When is this useful?"
	Injecting a custom boto3 client can make unit/snapshot testing easier, including SDK customizations.

### Customizing boto configuration

The **`config`** , **`boto3_session`**, and **`boto3_client`**  parameters enable you to pass in a custom [botocore config object](https://botocore.amazonaws.com/v1/documentation/api/latest/reference/config.html){target="_blank"}, [boto3 session](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/core/session.html){target="_blank"}, or  a [boto3 client](https://boto3.amazonaws.com/v1/documentation/api/latest/reference/core/boto3.html){target="_blank"} when constructing any of the built-in provider classes.

???+ tip
	You can use a custom session for retrieving parameters cross-account/region and for snapshot testing.

	When using VPC private endpoints, you can pass a custom client altogether. It's also useful for testing when injecting fake instances.

=== "custom_boto_session.py"
    ```python hl_lines="5 6"
    --8<-- "examples/parameters/src/custom_boto_session.py"
    ```

=== "custom_boto_config.py"
    ```python hl_lines="5 6"
    --8<-- "examples/parameters/src/custom_boto_config.py"
    ```

=== "custom_boto_client.py"
    ```python hl_lines="5 6"
    --8<-- "examples/parameters/src/custom_boto_client.py"
    ```

## Testing your code

### Mocking parameter values

For unit testing your applications, you can mock the calls to the parameters utility to avoid calling AWS APIs. This can be achieved in a number of ways - in this example, we use the [pytest monkeypatch fixture](https://docs.pytest.org/en/latest/how-to/monkeypatch.html){target="_blank"} to patch the `parameters.get_parameter` method:

=== "test_single_mock.py"
    ```python hl_lines="4 8"
    --8<-- "examples/parameters/tests/test_single_mock.py"
    ```

=== "single_mock.py"
    ```python
    --8<-- "examples/parameters/tests/src/single_mock.py"
    ```

If we need to use this pattern across multiple tests, we can avoid repetition by refactoring to use our own pytest fixture:

=== "test_with_fixture.py"
    ```python hl_lines="5 10"
    --8<-- "examples/parameters/tests/test_with_fixture.py"
    ```

Alternatively, if we need more fully featured mocking (for example checking the arguments passed to `get_parameter`), we
can use [unittest.mock](https://docs.python.org/3/library/unittest.mock.html){target="_blank"} from the python stdlib instead of pytest's `monkeypatch` fixture. In this example, we use the
[patch](https://docs.python.org/3/library/unittest.mock.html#unittest.mock.patch){target="_blank"} decorator to replace the `aws_lambda_powertools.utilities.parameters.get_parameter` function with a [MagicMock](https://docs.python.org/3/library/unittest.mock.html#unittest.mock.MagicMock){target="_blank"}
object named `get_parameter_mock`.

=== "test_with_monkeypatch.py"
    ```python hl_lines="7 12"
    --8<-- "examples/parameters/tests/test_with_monkeypatch.py"
    ```

### Clearing cache

Parameters utility caches all parameter values for performance and cost reasons. However, this can have unintended interference in tests using the same parameter name.

Within your tests, you can use `clear_cache` method available in [every provider](#built-in-provider-class). When using multiple providers or higher level functions like `get_parameter`, use `clear_caches` standalone function to clear cache globally.

=== "test_clear_cache_method.py"
    ```python hl_lines="8"
    --8<-- "examples/parameters/tests/test_clear_cache_method.py"
    ```

=== "test_clear_cache_global.py"
    ```python hl_lines="10"
    --8<-- "examples/parameters/tests/test_clear_cache_global.py"
    ```

=== "app.py"
    ```python
    --8<-- "examples/parameters/tests/src/app.py"
    ```
