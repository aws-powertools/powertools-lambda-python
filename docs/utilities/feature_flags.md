---
title: Feature flags
description: Utility
---

The feature flags utility provides a simple rule engine to define when one or multiple features should be enabled depending on the input.

???+ info
    When using `AppConfigStore`, we currently only support AppConfig using [freeform configuration profile](https://docs.aws.amazon.com/appconfig/latest/userguide/appconfig-creating-configuration-and-profile.html#appconfig-creating-configuration-and-profile-free-form-configurations){target="_blank"}  .

## Key features

* Define simple feature flags to dynamically decide when to enable a feature
* Fetch one or all feature flags enabled for a given application context
* Support for static feature flags to simply turn on/off a feature without rules
* Support for time based feature flags
* Bring your own Feature Flags Store Provider

## Terminology

Feature flags are used to modify behaviour without changing the application's code. These flags can be **static** or **dynamic**.

**Static flags**. Indicates something is simply `on` or `off`, for example `TRACER_ENABLED=True`.

**Dynamic flags**. Indicates something can have varying states, for example enable a list of premium features for customer X not Y.

???+ tip
    You can use [Parameters utility](parameters.md){target="_blank"} for static flags while this utility can do both static and dynamic feature flags.

???+ warning
    Be mindful that feature flags can increase the complexity of your application over time; use them sparingly.

If you want to learn more about feature flags, their variations and trade-offs, check these articles:

* [Feature Toggles (aka Feature Flags) - Pete Hodgson](https://martinfowler.com/articles/feature-toggles.html){target="_blank"}
* [AWS Lambda Feature Toggles Made Simple - Ran Isenberg](https://isenberg-ran.medium.com/aws-lambda-feature-toggles-made-simple-580b0c444233){target="_blank"}
* [Feature Flags Getting Started - CloudBees](https://www.cloudbees.com/blog/ultimate-feature-flag-guide){target="_blank"}

???+ note
    AWS AppConfig requires two API calls to fetch configuration for the first time. You can improve latency by consolidating your feature settings in a single [Configuration](https://docs.aws.amazon.com/appconfig/latest/userguide/appconfig-creating-configuration-and-profile.html){target="_blank"}.

## Getting started

### IAM Permissions

When using the default store `AppConfigStore`, your Lambda function IAM Role must have `appconfig:GetLatestConfiguration` and `appconfig:StartConfigurationSession` IAM permissions before using this feature.

### Required resources

By default, this utility provides [AWS AppConfig](https://docs.aws.amazon.com/appconfig/latest/userguide/what-is-appconfig.html){target="_blank"} as a configuration store.

The following sample infrastructure will be used throughout this documentation:

=== "template.yaml"

    ```yaml hl_lines="5 11 18 25 31-50 54"
    --8<-- "examples/feature_flags/sam/template.yaml"
    ```

=== "CDK"

    ```python hl_lines="11-22 24 29 35 42 50"
    import json

    import aws_cdk.aws_appconfig as appconfig
    from aws_cdk import core


    class SampleFeatureFlagStore(core.Construct):
        def __init__(self, scope: core.Construct, id_: str) -> None:
            super().__init__(scope, id_)

            features_config = {
                "premium_features": {
                    "default": False,
                    "rules": {
                        "customer tier equals premium": {
                            "when_match": True,
                            "conditions": [{"action": "EQUALS", "key": "tier", "value": "premium"}],
                        }
                    },
                },
                "ten_percent_off_campaign": {"default": True},
            }

            self.config_app = appconfig.CfnApplication(
                self,
                id="app",
                name="product-catalogue",
            )
            self.config_env = appconfig.CfnEnvironment(
                self,
                id="env",
                application_id=self.config_app.ref,
                name="dev-env",
            )
            self.config_profile = appconfig.CfnConfigurationProfile(
                self,
                id="profile",
                application_id=self.config_app.ref,
                location_uri="hosted",
                name="features",
            )
            self.hosted_cfg_version = appconfig.CfnHostedConfigurationVersion(
                self,
                "version",
                application_id=self.config_app.ref,
                configuration_profile_id=self.config_profile.ref,
                content=json.dumps(features_config),
                content_type="application/json",
            )
            self.app_config_deployment = appconfig.CfnDeployment(
                self,
                id="deploy",
                application_id=self.config_app.ref,
                configuration_profile_id=self.config_profile.ref,
                configuration_version=self.hosted_cfg_version.ref,
                deployment_strategy_id="AppConfig.AllAtOnce",
                environment_id=self.config_env.ref,
            )

    ```

### Evaluating a single feature flag

To get started, you'd need to initialize `AppConfigStore` and `FeatureFlags`. Then call `FeatureFlags` `evaluate` method to fetch, validate, and evaluate your feature.

The `evaluate` method supports two optional parameters:

* **context**: Value to be evaluated against each rule defined for the given feature
* **default**: Sentinel value to use in case we experience any issues with our store, or feature doesn't exist

=== "getting_started_single_feature_flag.py"

    ```python hl_lines="3 6 8 27 31"
    --8<-- "examples/feature_flags/src/getting_started_single_feature_flag.py"
    ```

=== "getting_started_single_feature_flag_payload.json"

    ```json hl_lines="3"
    --8<-- "examples/feature_flags/src/getting_started_single_feature_flag_payload.json"
    ```
=== "getting_started_single_feature_flag_features.json"

    ```json hl_lines="2 6 9-11"
    --8<-- "examples/feature_flags/src/getting_started_single_feature_flag_features.json"
    ```

#### Static flags

We have a static flag named `ten_percent_off_campaign`. Meaning, there are no conditional rules, it's either ON or OFF for all customers.

In this case, we could omit the `context` parameter and simply evaluate whether we should apply the 10% discount.

=== "getting_started_static_flag.py"

    ```python hl_lines="3 8 16"
    --8<-- "examples/feature_flags/src/getting_started_static_flag.py"
    ```
=== "getting_started_static_flag_payload.json"

    ```json hl_lines="2-3"
    --8<-- "examples/feature_flags/src/getting_started_static_flag_payload.json"
    ```

=== "getting_started_static_flag_features.json"

    ```json hl_lines="2-4"
    --8<-- "examples/feature_flags/src/getting_started_static_flag_features.json"
    ```

### Getting all enabled features

As you might have noticed, each `evaluate` call means an API call to the Store and the more features you have the more costly this becomes.

You can use `get_enabled_features` method for scenarios where you need a list of all enabled features according to the input context.

=== "getting_all_enabled_features.py"

    ```python hl_lines="2 9 26"
    --8<-- "examples/feature_flags/src/getting_all_enabled_features.py"
    ```

=== "getting_all_enabled_features_payload.json"

    ```json hl_lines="2 8"
    --8<-- "examples/feature_flags/src/getting_all_enabled_features_payload.json"
    ```

=== "getting_all_enabled_features_features.json"

    ```json hl_lines="2 8-12 17-18 20 27-28 30"
    --8<-- "examples/feature_flags/src/getting_all_enabled_features_features.json"
    ```

### Time based feature flags

Feature flags can also return enabled features based on time or datetime ranges.
This allows you to have features that are only enabled on certain days of the week, certain time
intervals or between certain calendar dates.

Use cases:

* Enable maintenance mode during a weekend
* Disable support/chat feature after working hours
* Launch a new feature on a specific date and time

You can also have features enabled only at certain times of the day for premium tier customers

=== "timebased_feature.py"

    ```python hl_lines="1 6 40"
    --8<-- "examples/feature_flags/src/timebased_feature.py"
    ```

=== "timebased_feature_event.json"

    ```json hl_lines="3"
    --8<-- "examples/feature_flags/src/timebased_feature_event.json"
    ```

=== "timebased_features.json"

    ```json hl_lines="9-11 14-21"
    --8<-- "examples/feature_flags/src/timebased_features.json"
    ```

You can also have features enabled only at certain times of the day.

=== "timebased_happyhour_feature.py"

    ```python hl_lines="1 6 29"
    --8<-- "examples/feature_flags/src/timebased_happyhour_feature.py"
    ```

=== "timebased_happyhour_features.json"

    ```json hl_lines="9-14"
    --8<-- "examples/feature_flags/src/timebased_happyhour_features.json"
    ```

You can also have features enabled only at specific days, for example: enable christmas sale discount during specific dates.

=== "datetime_feature.py"

    ```python hl_lines="1 6 31"
    --8<-- "examples/feature_flags/src/datetime_feature.py"
    ```

=== "datetime_features.json"

    ```json hl_lines="9-14"
    --8<-- "examples/feature_flags/src/datetime_features.json"
    ```

???+ info "How should I use timezones?"
    You can use any [IANA time zone](https://www.iana.org/time-zones){target="_blank"} (as originally specified
    in [PEP 615](https://peps.python.org/pep-0615/){target="_blank"}) as part of your rules definition.
    Powertools for AWS Lambda (Python) takes care of converting and calculate the correct timestamps for you.

    When using `SCHEDULE_BETWEEN_DATETIME_RANGE`, use timestamps without timezone information, and
    specify the timezone manually. This way, you'll avoid hitting problems with day light savings.

### Modulo Range Segmented Experimentation

Feature flags can also be used to run experiments on a segment of users based on modulo range conditions on context variables.
This allows you to have features that are only enabled for a certain segment of users, comparing across multiple variants
of the same experiment.

Use cases:

* Enable an experiment for a percentage of users
* Scale up an experiment incrementally in production - canary release
* Run multiple experiments or variants simultaneously by assigning a spectrum segment to each experiment variant.

The modulo range condition takes three values - `BASE`, `START` and `END`.

The condition evaluates `START <= CONTEXT_VALUE % BASE <= END`.

=== "modulo_range_feature.py"

    ```python hl_lines="1 6 38"
    --8<-- "examples/feature_flags/src/modulo_range_feature.py"
    ```

=== "modulo_range_feature_event.json"

    ```json hl_lines="2"
    --8<-- "examples/feature_flags/src/modulo_range_feature_event.json"
    ```

=== "modulo_range_features.json"

    ```json hl_lines="13-21"
    --8<-- "examples/feature_flags/src/modulo_range_features.json"
    ```

You can run multiple experiments on your users with the spectrum of your choice.

=== "modulo_range_multiple_feature.py"

    ```python hl_lines="1 6 67"
    --8<-- "examples/feature_flags/src/modulo_range_multiple_feature.py"
    ```

=== "modulo_range_multiple_features.json"

    ```json hl_lines="9-16 23-31 37-45"
    --8<-- "examples/feature_flags/src/modulo_range_multiple_features.json"
    ```

### Beyond boolean feature flags

???+ info "When is this useful?"
    You might have a list of features to unlock for premium customers, unlock a specific set of features for admin users, etc.

Feature flags can return any JSON values when `boolean_type` parameter is set to `false`. These can be dictionaries, list, string, integers, etc.

=== "beyond_boolean.py"

    ```python hl_lines="3 8 16"
    --8<-- "examples/feature_flags/src/beyond_boolean.py"
    ```

=== "beyond_boolean_payload.json"

    ```json hl_lines="3"
    --8<-- "examples/feature_flags/src/beyond_boolean_payload.json"
    ```

=== "beyond_boolean_features.json"

    ```json hl_lines="7-11 14-16"
    --8<-- "examples/feature_flags/src/beyond_boolean_features.json"
    ```

## Advanced

### Adjusting in-memory cache

By default, we cache configuration retrieved from the Store for 5 seconds for performance and reliability reasons.

You can override `max_age` parameter when instantiating the store.

=== "getting_started_with_cache.py"

    ```python hl_lines="6"
    --8<-- "examples/feature_flags/src/getting_started_with_cache.py"
    ```
=== "getting_started_with_cache_payload.json"

    ```json hl_lines="2-3"
    --8<-- "examples/feature_flags/src/getting_started_with_cache_payload.json"
    ```

=== "getting_started_with_cache_features.json"

    ```json hl_lines="2-4"
    --8<-- "examples/feature_flags/src/getting_started_with_cache_features.json"
    ```

### Getting fetched configuration

???+ info "When is this useful?"
	You might have application configuration in addition to feature flags in your store.

	This means you don't need to make another call only to fetch app configuration.

You can access the configuration fetched from the store via `get_raw_configuration` property within the store instance.

=== "getting_stored_features.py"

    ```python hl_lines="9"
    --8<-- "examples/feature_flags/src/getting_stored_features.py"
    ```

### Schema

This utility expects a certain schema to be stored as JSON within AWS AppConfig.

#### Features

A feature can simply have its name and a `default` value. This is either on or off, also known as a [static flag](#static-flags).

=== "minimal_schema.json"

    ```json hl_lines="2-3 5-7"
    --8<-- "examples/feature_flags/src/minimal_schema.json"
    ```

If you need more control and want to provide context such as user group, permissions, location, etc., you need to add rules to your feature flag configuration.

#### Rules

When adding `rules` to a feature, they must contain:

1. A rule name as a key
2. `when_match` boolean or JSON value that should be used when conditions match
3. A list of `conditions` for evaluation

=== "feature_with_rules.json"

    ```json hl_lines="4-11 19-26"
    --8<-- "examples/feature_flags/src/feature_with_rules.json"
    ```

You can have multiple rules with different names. The rule engine will return the first result `when_match` of the matching rule configuration, or `default` value when none of the rules apply.

#### Conditions

The `conditions` block is a list of conditions that contain `action`, `key`, and `value` keys:

=== "conditions.json"

    ```json hl_lines="5-7"
    --8<-- "examples/feature_flags/src/conditions.json"
    ```

The `action` configuration can have the following values, where the expressions **`a`** is the `key` and **`b`** is the `value` above:

| Action                              | Equivalent expression                                    |
| ----------------------------------- | -------------------------------------------------------- |
| **EQUALS**                          | `lambda a, b: a == b`                                    |
| **NOT_EQUALS**                      | `lambda a, b: a != b`                                    |
| **KEY_GREATER_THAN_VALUE**          | `lambda a, b: a > b`                                     |
| **KEY_GREATER_THAN_OR_EQUAL_VALUE** | `lambda a, b: a >= b`                                    |
| **KEY_LESS_THAN_VALUE**             | `lambda a, b: a < b`                                     |
| **KEY_LESS_THAN_OR_EQUAL_VALUE**    | `lambda a, b: a <= b`                                    |
| **STARTSWITH**                      | `lambda a, b: a.startswith(b)`                           |
| **ENDSWITH**                        | `lambda a, b: a.endswith(b)`                             |
| **KEY_IN_VALUE**                    | `lambda a, b: a in b`                                    |
| **KEY_NOT_IN_VALUE**                | `lambda a, b: a not in b`                                |
| **VALUE_IN_KEY**                    | `lambda a, b: b in a`                                    |
| **VALUE_NOT_IN_KEY**                | `lambda a, b: b not in a`                                |
| **SCHEDULE_BETWEEN_TIME_RANGE**     | `lambda a, b: b.start <= time(a) <= b.end`        |
| **SCHEDULE_BETWEEN_DATETIME_RANGE** | `lambda a, b: b.start <= datetime(a) <= b.end` |
| **SCHEDULE_BETWEEN_DAYS_OF_WEEK**   | `lambda a, b: day_of_week(a) in b`                       |
| **MODULO_RANGE**                    | `lambda a, b: b.start <= a % b.base <= b.end`            |

???+ info
    The `key` and `value` will be compared to the input from the `context` parameter.

???+ "Time based keys"

    For time based keys, we provide a list of predefined keys. These will automatically get converted to the corresponding timestamp on each invocation of your Lambda function.

    | Key                 | Meaning                                                                                   |
    | ------------------- | ----------------------------------------------------------------------------------------- |
    | CURRENT_TIME        | The current time, 24 hour format (HH:mm)                                                  |
    | CURRENT_DATETIME    | The current datetime ([ISO8601](https://en.wikipedia.org/wiki/ISO_8601){target="_blank"}) |
    | CURRENT_DAY_OF_WEEK | The current day of the week (Monday-Sunday)                                               |

    If not specified, the timezone used for calculations will be UTC.

**For multiple conditions**, we will evaluate the list of conditions as a logical `AND`, so all conditions needs to match to return `when_match` value.

#### Rule engine flowchart

Now that you've seen all properties of a feature flag schema, this flowchart describes how the rule engine decides what value to return.

![Rule engine ](../media/feature_flags_diagram.png)

### Envelope

There are scenarios where you might want to include feature flags as part of an existing application configuration.

For this to work, you need to use a JMESPath expression via the `envelope` parameter to extract that key as the feature flags configuration.

=== "extracting_envelope.py"

    ```python hl_lines="7"
    --8<-- "examples/feature_flags/src/extracting_envelope.py"
    ```

=== "extracting_envelope_payload.json"

    ```json hl_lines="2-3"
    --8<-- "examples/feature_flags/src/extracting_envelope_payload.json"
    ```

=== "extracting_envelope_features.json"

    ```json hl_lines="6"
    --8<-- "examples/feature_flags/src/extracting_envelope_features.json"
    ```

### Built-in store provider

#### AppConfig

AppConfig store provider fetches any JSON document from AWS AppConfig.

These are the available options for further customization.

| Parameter            | Default          | Description                                                                                                                                            |
| -------------------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **environment**      | `""`             | AWS AppConfig Environment, e.g. `dev`                                                                                                                  |
| **application**      | `""`             | AWS AppConfig Application, e.g. `product-catalogue`                                                                                                    |
| **name**             | `""`             | AWS AppConfig Configuration name, e.g `features`                                                                                                       |
| **envelope**         | `None`           | JMESPath expression to use to extract feature flags configuration from AWS AppConfig configuration                                                     |
| **max_age**          | `5`              | Number of seconds to cache feature flags configuration fetched from AWS AppConfig                                                                      |
| **sdk_config**       | `None`           | [Botocore Config object](https://botocore.amazonaws.com/v1/documentation/api/latest/reference/config.html){target="_blank"}                            |
| **jmespath_options** | `None`           | For advanced use cases when you want to bring your own [JMESPath functions](https://github.com/jmespath/jmespath.py#custom-functions){target="_blank"} |
| **logger**           | `logging.Logger` | Logger to use for debug.  You can optionally supply an instance of Powertools for AWS Lambda (Python) Logger.                                          |

=== "appconfig_provider_options.py"

    ```python hl_lines="9 13-17 20 28-30"
    --8<-- "examples/feature_flags/src/appconfig_provider_options.py"
    ```

=== "appconfig_provider_options_payload.json"

    ```json hl_lines="2 3"
    --8<-- "examples/feature_flags/src/appconfig_provider_options_payload.json"
    ```

=== "appconfig_provider_options_features.json"

    ```json hl_lines="6-9"
    --8<-- "examples/feature_flags/src/appconfig_provider_options_features.json"
    ```

### Create your own store provider

You can create your own custom FeatureFlags store provider by inheriting the `StoreProvider` class, and implementing both `get_raw_configuration()` and `get_configuration()` methods to retrieve the configuration from your custom store.

* **`get_raw_configuration()`** – get the raw configuration from the store provider and return the parsed JSON dictionary
* **`get_configuration()`** – get the configuration from the store provider, parsing it as a JSON dictionary. If an envelope is set, extract the envelope data

Here are an example of implementing a custom store provider using Amazon S3, a popular object storage.

???+ note
    This is just one example of how you can create your own store provider. Before creating a custom store provider, carefully evaluate your requirements and consider factors such as performance, scalability, and ease of maintenance.

=== "working_with_own_s3_store_provider.py"

    ```python hl_lines="3 8 10"
    --8<-- "examples/feature_flags/src/working_with_own_s3_store_provider.py"
    ```

=== "custom_s3_store_provider.py"

    ```python hl_lines="33 37"
    --8<-- "examples/feature_flags/src/custom_s3_store_provider.py"
    ```

=== "working_with_own_s3_store_provider_payload.json"

    ```json hl_lines="2 3"
    --8<-- "examples/feature_flags/src/working_with_own_s3_store_provider_payload.json"
    ```

=== "working_with_own_s3_store_provider_features.json"

    ```json hl_lines="2-4"
    --8<-- "examples/feature_flags/src/working_with_own_s3_store_provider_features.json"
    ```

## Testing your code

You can unit test your feature flags locally and independently without setting up AWS AppConfig.

`AppConfigStore` only fetches a JSON document with a specific schema. This allows you to mock the response and use it to verify the rule evaluation.

???+ warning
    This excerpt relies on `pytest` and `pytest-mock` dependencies.

=== "Testing your code"

    ```python hl_lines="11-13"
    --8<-- "examples/feature_flags/src/getting_started_with_tests.py"
    ```

## Feature flags vs Parameters vs Env vars

| Method                                                                                                                | When to use                                                                                                             | Requires new deployment on changes | Supported services                                    |
| --------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ---------------------------------- | ----------------------------------------------------- |
| **[Environment variables](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html){target="_blank"}** | Simple configuration that will rarely if ever change, because changing it requires a Lambda function deployment.        | Yes                                | Lambda                                                |
| **[Parameters utility](parameters.md){target="_blank"}**                                                                               | Access to secrets, or fetch parameters in different formats from AWS System Manager Parameter Store or Amazon DynamoDB. | No                                 | Parameter Store, DynamoDB, Secrets Manager, AppConfig |
| **Feature flags utility**                                                                                             | Rule engine to define when one or multiple features should be enabled depending on the input.                           | No                                 | AppConfig                                             |
