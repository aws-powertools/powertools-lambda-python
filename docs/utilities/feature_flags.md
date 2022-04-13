---
title: Feature flags
description: Utility
---

???+ note
    This is currently in Beta, as we might change Store parameters in the next release.

The feature flags utility provides a simple rule engine to define when one or multiple features should be enabled depending on the input.

## Terminology

Feature flags are used to modify behaviour without changing the application's code. These flags can be **static** or **dynamic**.

**Static flags**. Indicates something is simply `on` or `off`, for example `TRACER_ENABLED=True`.

**Dynamic flags**. Indicates something can have varying states, for example enable a list of premium features for customer X not Y.

???+ tip
    You can use [Parameters utility](parameters.md) for static flags while this utility can do both static and dynamic feature flags.

???+ warning
    Be mindful that feature flags can increase the complexity of your application over time; use them sparingly.

If you want to learn more about feature flags, their variations and trade-offs, check these articles:

* [Feature Toggles (aka Feature Flags) - Pete Hodgson](https://martinfowler.com/articles/feature-toggles.html)
* [AWS Lambda Feature Toggles Made Simple - Ran Isenberg](https://isenberg-ran.medium.com/aws-lambda-feature-toggles-made-simple-580b0c444233)
* [Feature Flags Getting Started - CloudBees](https://www.cloudbees.com/blog/ultimate-feature-flag-guide)

## Key features

* Define simple feature flags to dynamically decide when to enable a feature
* Fetch one or all feature flags enabled for a given application context
* Support for static feature flags to simply turn on/off a feature without rules

## Getting started

### IAM Permissions

Your Lambda function must have `appconfig:GetConfiguration` IAM permission in order to fetch configuration from AWS AppConfig.

### Required resources

By default, this utility provides [AWS AppConfig](https://docs.aws.amazon.com/appconfig/latest/userguide/what-is-appconfig.html) as a configuration store.

The following sample infrastructure will be used throughout this documentation:

=== "template.yaml"

    ```yaml hl_lines="5 11 18 25 31-50 54"
    --8<-- "docs/examples/utilities/feature_flags/template.yml"
    ```

=== "CDK"

    ```python hl_lines="11-22 24 29 35 42 50"
    --8<-- "docs/examples/utilities/feature_flags/cdk_app.py"
    ```

### Evaluating a single feature flag

To get started, you'd need to initialize `AppConfigStore` and `FeatureFlags`. Then call `FeatureFlags` `evaluate` method to fetch, validate, and evaluate your feature.

The `evaluate` method supports two optional parameters:

* **context**: Value to be evaluated against each rule defined for the given feature
* **default**: Sentinel value to use in case we experience any issues with our store, or feature doesn't exist

=== "app.py"

    ```python hl_lines="3 9 14 18-23"
    --8<-- "docs/examples/utilities/feature_flags/single_feature_flag.py"
    ```

=== "event.json"

    ```json hl_lines="3"
    {
        "username": "lessa",
        "tier": "premium",
        "basked_id": "random_id"
    }
    ```
=== "features.json"

    ```json hl_lines="2 6 9-11"
    {
        "premium_features": {
            "default": false,
            "rules": {
                "customer tier equals premium": {
                    "when_match": true,
                    "conditions": [
                        {
                            "action": "EQUALS",
                            "key": "tier",
                            "value": "premium"
                        }
                    ]
                }
            }
        },
        "ten_percent_off_campaign": {
            "default": false
        }
    }
    ```

#### Static flags

We have a static flag named `ten_percent_off_campaign`. Meaning, there are no conditional rules, it's either ON or OFF for all customers.

In this case, we could omit the `context` parameter and simply evaluate whether we should apply the 10% discount.

=== "app.py"

    ```python hl_lines="13-16"
    --8<-- "docs/examples/utilities/feature_flags/static_flag.py"
    ```

=== "features.json"

    ```json hl_lines="2-3"
    {
        "ten_percent_off_campaign": {
            "default": false
        }
    }
    ```

### Getting all enabled features

As you might have noticed, each `evaluate` call means an API call to the Store and the more features you have the more costly this becomes.

You can use `get_enabled_features` method for scenarios where you need a list of all enabled features according to the input context.

=== "app.py"

    ```python hl_lines="16-19 22"
    --8<-- "docs/examples/utilities/feature_flags/get_enabled_features.py"
    ```

=== "event.json"

    ```json hl_lines="2 8"
    {
        "body": "{\"username\": \"lessa\", \"tier\": \"premium\", \"basked_id\": \"random_id\"}",
        "resource": "/products",
        "path": "/products",
        "httpMethod": "GET",
        "isBase64Encoded": false,
        "headers": {
            "CloudFront-Viewer-Country": "NL"
        }
    }
    ```
=== "features.json"

    ```json hl_lines="17-18 20 27-29"
    {
        "premium_features": {
            "default": false,
            "rules": {
                "customer tier equals premium": {
                    "when_match": true,
                    "conditions": [
                        {
                            "action": "EQUALS",
                            "key": "tier",
                            "value": "premium"
                        }
                    ]
                }
            }
        },
        "ten_percent_off_campaign": {
            "default": true
        },
        "geo_customer_campaign": {
            "default": false,
            "rules": {
                "customer in temporary discount geo": {
                    "when_match": true,
                    "conditions": [
                        {
                            "action": "KEY_IN_VALUE",
                            "key": "CloudFront-Viewer-Country",
                            "value": ["NL", "IE", "UK", "PL", "PT"]
                        }
                    ]
                }
            }
        }
    }
    ```

### Beyond boolean feature flags

???+ info "When is this useful?"
    You might have a list of features to unlock for premium customers, unlock a specific set of features for admin users, etc.

Feature flags can return any JSON values when `boolean_type` parameter is set to `false`. These can be dictionaries, list, string, integers, etc.

=== "app.py"

    ```python hl_lines="3 9 14 17 22"
    --8<-- "docs/examples/utilities/feature_flags/non_boolean_flag.py"
    ```

=== "event.json"

    ```json hl_lines="3"
    {
        "username": "lessa",
        "tier": "premium",
        "basked_id": "random_id"
    }
    ```
=== "features.json"

    ```json hl_lines="3-4 7"
    {
        "premium_features": {
            "boolean_type": false,
            "default": [],
            "rules": {
                "customer tier equals premium": {
                    "when_match": ["no_ads", "no_limits", "chat"],
                    "conditions": [
                        {
                            "action": "EQUALS",
                            "key": "tier",
                            "value": "premium"
                        }
                    ]
                }
            }
        }
    }
    ```

## Advanced

### Adjusting in-memory cache

By default, we cache configuration retrieved from the Store for 5 seconds for performance and reliability reasons.

You can override `max_age` parameter when instantiating the store.

=== "app.py"

    ```python hl_lines="7"
    --8<-- "docs/examples/utilities/feature_flags/cache_config.py"
    ```

### Getting fetched configuration

???+ info "When is this useful?"
	You might have application configuration in addition to feature flags in your store.

	This means you don't need to make another call only to fetch app configuration.

You can access the configuration fetched from the store via `get_raw_configuration` property within the store instance.

=== "app.py"

    ```python hl_lines="12"
    --8<-- "docs/examples/utilities/feature_flags/get_raw_configuration.py"
    ```

### Schema

This utility expects a certain schema to be stored as JSON within AWS AppConfig.

#### Features

A feature can simply have its name and a `default` value. This is either on or off, also known as a [static flag](#static-flags).

```json hl_lines="2-3 5-7" title="minimal_schema.json"
{
    "global_feature": {
        "default": true
    },
    "non_boolean_global_feature": {
        "default": {"group": "read-only"},
        "boolean_type": false
    },
}
```

If you need more control and want to provide context such as user group, permissions, location, etc., you need to add rules to your feature flag configuration.

#### Rules

When adding `rules` to a feature, they must contain:

1. A rule name as a key
2. `when_match` boolean or JSON value that should be used when conditions match
3. A list of `conditions` for evaluation

 ```json hl_lines="4-11 19-26" title="feature_with_rules.json"
 {
     "premium_feature": {
         "default": false,
         "rules": {
             "customer tier equals premium": {
                 "when_match": true,
                 "conditions": [
                     {
                         "action": "EQUALS",
                         "key": "tier",
                         "value": "premium"
                     }
                 ]
             }
         }
     },
     "non_boolean_premium_feature": {
         "default": [],
         "rules": {
             "customer tier equals premium": {
                 "when_match": ["remove_limits", "remove_ads"],
                 "conditions": [
                     {
                         "action": "EQUALS",
                         "key": "tier",
                         "value": "premium"
                     }
                 ]
             }
         }
     }
 }
 ```

You can have multiple rules with different names. The rule engine will return the first result `when_match` of the matching rule configuration, or `default` value when none of the rules apply.

#### Conditions

The `conditions` block is a list of conditions that contain `action`, `key`, and `value` keys:

```json  hl_lines="5-7" title="conditions.json"
{
	...
	"conditions": [
		{
			"action": "EQUALS",
			"key": "tier",
			"value": "premium"
		}
	]
}
```

The `action` configuration can have the following values, where the expressions **`a`** is the `key` and **`b`** is the `value` above:

Action | Equivalent expression
------------------------------------------------- | ---------------------------------------------------------------------------------
**EQUALS** | `lambda a, b: a == b`
**NOT_EQUALS** | `lambda a, b: a != b`
**KEY_GREATER_THAN_VALUE** | `lambda a, b: a > b`
**KEY_GREATER_THAN_OR_EQUAL_VALUE** | `lambda a, b: a >= b`
**KEY_LESS_THAN_VALUE** | `lambda a, b: a < b`
**KEY_LESS_THAN_OR_EQUAL_VALUE** | `lambda a, b: a <= b`
**STARTSWITH** | `lambda a, b: a.startswith(b)`
**ENDSWITH** | `lambda a, b: a.endswith(b)`
**KEY_IN_VALUE** | `lambda a, b: a in b`
**KEY_NOT_IN_VALUE** | `lambda a, b: a not in b`
**VALUE_IN_KEY** | `lambda a, b: b in a`
**VALUE_NOT_IN_KEY** | `lambda a, b: b not in a`


???+ info
    The `**key**` and `**value**` will be compared to the input from the `**context**` parameter.

**For multiple conditions**, we will evaluate the list of conditions as a logical `AND`, so all conditions needs to match to return `when_match` value.

#### Rule engine flowchart

Now that you've seen all properties of a feature flag schema, this flowchart describes how the rule engine decides what value to return.

![Rule engine ](../media/feature_flags_diagram.png)

### Envelope

There are scenarios where you might want to include feature flags as part of an existing application configuration.

For this to work, you need to use a JMESPath expression via the `envelope` parameter to extract that key as the feature flags configuration.

=== "app.py"

    ```python hl_lines="7"
    --8<-- "docs/examples/utilities/feature_flags/envelope.py"
    ```

=== "configuration.json"

    ```json hl_lines="6"
    {
        "logging": {
            "level": "INFO",
            "sampling_rate": 0.1
        },
        "feature_flags": {
            "premium_feature": {
                "default": false,
                "rules": {
                    "customer tier equals premium": {
                        "when_match": true,
                        "conditions": [
                            {
                                "action": "EQUALS",
                                "key": "tier",
                                "value": "premium"
                            }
                        ]
                    }
                }
            },
            "feature2": {
                "default": false
            }
        }
    }
    ```

### Built-in store provider

???+ info
    For GA, you'll be able to bring your own store.

#### AppConfig

AppConfig store provider fetches any JSON document from AWS AppConfig.

These are the available options for further customization.

Parameter | Default | Description
------------------------------------------------- | ------------------------------------------------- | ---------------------------------------------------------------------------------
**environment** | `""` | AWS AppConfig Environment, e.g. `test`
**application** | `""` | AWS AppConfig Application
**name** | `""` | AWS AppConfig Configuration name
**envelope** | `None` | JMESPath expression to use to extract feature flags configuration from AWS AppConfig configuration
**max_age** | `5` | Number of seconds to cache feature flags configuration fetched from AWS AppConfig
**sdk_config** | `None` | [Botocore Config object](https://botocore.amazonaws.com/v1/documentation/api/latest/reference/config.html){target="_blank"}
**jmespath_options** | `None` | For advanced use cases when you want to bring your own [JMESPath functions](https://github.com/jmespath/jmespath.py#custom-functions){target="_blank"}
**logger** | `logging.Logger` | Logger to use for debug.  You can optionally supply an instance of Powertools Logger.

```python hl_lines="18-24" title="AppConfigStore sample"
--8<-- "docs/examples/utilities/feature_flags/app_config.py"
```

## Testing your code

You can unit test your feature flags locally and independently without setting up AWS AppConfig.

`AppConfigStore` only fetches a JSON document with a specific schema. This allows you to mock the response and use it to verify the rule evaluation.

???+ warning
    This excerpt relies on `pytest` and `pytest-mock` dependencies.

```python hl_lines="7-9" title="Unit testing feature flags"
--8<-- "docs/examples/utilities/feature_flags/unit_test.py"
```

## Feature flags vs Parameters vs env vars

Method | When to use | Requires new deployment on changes | Supported services
------------------------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------- | -------------------------------------------------
**[Environment variables](https://docs.aws.amazon.com/lambda/latest/dg/configuration-envvars.html){target="_blank"}** | Simple configuration that will rarely if ever change, because changing it requires a Lambda function deployment. | Yes | Lambda
**[Parameters utility](parameters.md)** | Access to secrets, or fetch parameters in different formats from AWS System Manager Parameter Store or Amazon DynamoDB. | No | Parameter Store, DynamoDB, Secrets Manager, AppConfig
**Feature flags utility** | Rule engine to define when one or multiple features should be enabled depending on the input. | No | AppConfig

## Deprecation list when GA

Breaking change | Recommendation
------------------------------------------------- | ---------------------------------------------------------------------------------
`IN` RuleAction | Use `KEY_IN_VALUE` instead
`NOT_IN` RuleAction | Use `KEY_NOT_IN_VALUE` instead
`get_enabled_features` | Return type changes from `List[str]` to `Dict[str, Any]`. New return will contain a list of features enabled and their values. List of enabled features will be in `enabled_features` key to keep ease of assertion we have in Beta.
`boolean_type` Schema | This **might** not be necessary anymore before we go GA. We will return either the `default` value when there are no rules as well as `when_match` value. This will simplify on-boarding if we can keep the same set of validations already offered.
