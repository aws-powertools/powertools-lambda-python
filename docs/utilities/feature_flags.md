---
title: Feature flags description: Utility
---

The feature flags utility provides a simple rule engine to define when one or multiple features should be enabled
depending on the input.

!!! tip "For simpler use cases where a feature is simply on or off for all users, use [Parameters](parameters.md)
utility instead."

## Terminology

Feature flags are used to modify a system behaviour without having to change their code. These flags can be static or
dynamic.

**Static feature flags** are commonly used for long-lived behaviours that will rarely change, for
example `TRACER_ENABLED=True`. These are better suited for [Parameters utility](parameters.md).

**Dynamic feature flags** are typically used for experiments where you'd want to enable a feature for a limited set of
customers, for example A/B testing and Canary releases. These are better suited for this utility, as you can create
multiple conditions on whether a feature flag should be `True` or `False`.

That being said, be mindful that feature flags can increase your application complexity over time if you're not careful;
use them sparingly.

If you want to learn more about feature flags, differen types and trade-offs, check this articles:

* [Feature Toggles (aka Feature Flags) - Pete Hodgson](https://martinfowler.com/articles/feature-toggles.html)
* [AWS Lambda Feature Toggles Made Simple - Ran Isenberg](https://isenberg-ran.medium.com/aws-lambda-feature-toggles-made-simple-580b0c444233)
* [Feature Flags Getting Started - CloudBees](https://www.cloudbees.com/blog/ultimate-feature-flag-guide)

## Key features

* Define simple feature flags to dynamically decide when to enable a feature
* Fetch one or all feature flags enabled for a given application context
* Bring your own configuration store

## Getting started

### IAM Permissions

Because powertools needs to fetch the configuration from the AppConfig, you need to add `appconfig:GetConfiguration`
action to your function.

### Required resources

By default, this utility
provides [AWS AppConfig](https://docs.aws.amazon.com/appconfig/latest/userguide/what-is-appconfig.html) as a
configuration store. To create a dedicate you can use this cloudformation template:

=== "template.yaml"

    ```yaml
    AWSTemplateFormatVersion: "2010-09-09"
    Description: A sample template
    Resources:
      FeatureStoreApp:
        Type: AWS::AppConfig::Application
        Properties:
          Description: "AppConfig Appliction for feature toggles"
          Name: my-app

      FeatureStoreDevEnv:
        Type: AWS::AppConfig::Environment
        Properties:
          ApplicationId: !Ref FeatureStoreApp
          Description: "Development Environment for the App Config Store"
          Name: "development"

      FeatureStoreConfigProfile:
        Type: AWS::AppConfig::ConfigurationProfile
        Properties:
          ApplicationId: !Ref FeatureStoreApp
          Name: "MyTestProfile"
          LocationUri: "hosted"

      HostedConfigVersion:
        Type: AWS::AppConfig::HostedConfigurationVersion
        Properties:
          ApplicationId: !Ref FeatureStoreApp
          ConfigurationProfileId: !Ref FeatureStoreConfigProfile
          Description: 'A sample hosted configuration version'
          Content: |
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
                  "feature2": {
                    "default": true
                  }
              }
          ContentType: 'application/json'

      ConfigDeployment:
        Type: AWS::AppConfig::Deployment
        Properties:
          ApplicationId: !Ref FeatureStoreApp
          ConfigurationProfileId: !Ref FeatureStoreConfigProfile
          ConfigurationVersion: !Ref HostedConfigVersion
          DeploymentStrategyId: "AppConfig.AllAtOnce"
          EnvironmentId: !Ref FeatureStoreDevEnv
    ```

=== "CDK"

    ```typescript
    import * as cdk from '@aws-cdk/core';
    import {
        CfnApplication,
        CfnConfigurationProfile, CfnDeployment,
        CfnEnvironment,
        CfnHostedConfigurationVersion
    } from "@aws-cdk/aws-appconfig";

    export class CdkStack extends cdk.Stack {
        constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
            super(scope, id, props);

            const featureConfig = {
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
                "feature2": {
                    "default": true
                }
            }

            const app = new CfnApplication(this, "app", {name: "productapp"});
            const env = new CfnEnvironment(this, "env", {
                applicationId: app.ref,
                name: "dev-env"
            });

            const configProfile = new CfnConfigurationProfile(this, "profile", {
                applicationId: app.ref,
                locationUri: "hosted",
                name: "configProfile"
            });


            const hostedConfigVersion = new CfnHostedConfigurationVersion(this, "version", {
                applicationId: app.ref,
                configurationProfileId: configProfile.ref,
                content: JSON.stringify(featureConfig),
                contentType: "application/json"
            });

            new CfnDeployment(this, "deploy", {
                applicationId: app.ref,
                configurationProfileId: configProfile.ref,
                configurationVersion: hostedConfigVersion.ref,
                deploymentStrategyId: "AppConfig.AllAtOnce",
                environmentId: env.ref
            });
        }
    }
    ```

The `Content` parameter is a json structure of the feature flags and rules.

TODO: add steps to create new version and new deployment for the config

TODO: add CDK example

### Use feature flag store

After you have created and configured `AppConfigStore` and added your feature configuraiton you can use the feature
flags in your code:

=== "app.py"

    ```python
    app_config = AppConfigStore(
        environment="dev",
        application="product-catalogue",
        name="features"
    )
    feature_flags = FeatureFlags(store=app_config)
    ctx = {"username": "lessa", "tier": "premium", "location": "NL"}

    has_premium_features: bool = feature_flags.evaluate(name="premium_features",
                                                        context=ctx,
                                                        default=False)
    ```

=== "features.json"

    ```json
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
      }
    }
    ```

### Evaluating a single feature flag

To fetch a single feature, setup the `FeatureFlags` instance and call the `evaluate` method.

=== "app.py"

    ```python
      feature_flags = FeatureFlags(store=app_config)

      new_feature_active: bool = feature_flags.evaluate(name="new_feature",
                                                          default=False)
    ```

=== "features.json"

    ```json
      {
        "new_feature": {
          "default": true
        }
      }
    ```

In this example the feature flag is **static**, which mean it will be evaluated without any additional context such as
user or location. If you want to have **dynamic** feature flags that only works for specific user group or other contex
aware information you need to pass a context object and add rules to your feature configuration.

=== "app.py"

    ```pyhthon
    feature_flags = FeatureFlags(store=app_config)
    ctx = {"username": "lessa", "tier": "premium", "location": "NL"}

    has_premium_features: bool = feature_flags.evaluate(name="premium_features",
                                                        context=ctx,
                                                        default=False
    ```

=== "features.json"

    ```json
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
      }
    }
    ```

### Get all enabled features

In cases where you need to get a list of all the features that are enabled according to the input context you can
use `get_enabled_features` method:

=== "app.py"

    ```python
    feature_flags = FeatureFlags(store=app_config)
    ctx = {"username": "lessa", "tier": "premium", "location": "NL"}

    all_features: list[str] = feature_flags.get_enabled_features(context=ctx)
    # all_features is evaluated to ["feautre1", "feature2"]
    ```

=== "features.json"

    ```json hl_lines="2 6"
    {
      "feature1": {
        "default": false,
        "rules": {...}
        },
      "feature2": {
        "default": false,
        "rules": {...}
        },
      ...
      }
    }
    ```

As a result you will get a list of all the names of the features from your feature flags configuration.

### Feature flags schema

When using the feature flags utility powertools expects specific schema stored in your AppConfig configuration. The
minimal requirement is the name of the feature and the default value, for example:

```json
{
  "global_feature": {
    "default": true
  }
}
```

This is a static flag that will be applied to every evaluation within your code. If you need more control and want to
provide context such as user group, permisisons, location or other information you need to add rules to your feature
flag configuration.

#### Rules

To use feature flags dynamically you can configure rules in your feature flags configuration and pass context
to `evaluate`. The rules block must have:

* rule name as a key
* value when the condition is met
* list conditions for evaluation

```json hl_lines="4-11"

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
  }
}
```

You can have multiple rules with different names. The powertools will return the first result `when_match` of the
matching rule configuration or `default` value when none of the rules apply.

#### Conditions

The conditions block is a list of `action`, `key` `value`:

```json
{
  "action": "EQUALS",
  "key": "tier",
  "value": "premium"
}
```

The `action` configuration can have 5 different values: `EQUALS`, `STARTSWITH`, `ENDSWITH`, `IN`, `NOT_IN`. The `key`
and `value` will be compared to the input from the context parameter.

If you have multiple conditions powertools will evaluate the list of conditions as a logical AND, so all conditions
needs to be matched to return `when_match` value.

=== "features.json"

    ```json  hl_lines="10-11"
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
      }
    }
    ```

=== "app.py"

    ```python  hl_lines="2"
        feature_flags = FeatureFlags(store=app_config)
        ctx = {"username": "lessa", "tier": "premium", "location": "NL"}

        has_premium_features: bool = feature_flags.evaluate(name="premium_features",
                                                            context=ctx,
                                                            default=False
    ```

## Advanced

### Adjusting in-memory cache
Similar to other utilities you can set the number of seconds the `AppConfigProvider` should cache the configuration.
This will ensure that powertools will keep a configuration for up to `case_seconds` seconds between Lambda invocation and will not make an API call each time.

```python hl_lines="5"
app_config = AppConfigStore(
    environment="test",
    application="powertools",
    name="test_conf_name",
    cache_seconds=300
)
```

### Envelope
In previous examples the schema for feature flags was a top level element in the json document.
In some cases it can be embedded as a part of bigger configuration on a deeper nested level, for example:

```json
{
  "logging" {...},
  "features": {
    "feature_flags": {
        "feature1": {
          "default": false,
          "rules": {...}
          },
        "feature2": {
          "default": false,
          "rules": {...}
          },
        ...
        }
      }
  }
}
```

This schema would not work with the default `AppConfigProvider` because the feature configuration is not a top level element.
Therefore, you need to pass a correct JMESPath by using the `envelope` parameter.

```python hl_lines="5"
app_config = AppConfigStore(
    environment="test",
    application="powertools",
    name="test_conf_name",
    envelope = "features.feature_flags"
)
```

### Built-in store provider
Powertools currently support only `AppConfig` store provider out of the box.
If you have your own store and want to use it with `FeatureFlags`, you need to extend from `StoreProvider` class and implement your `get_configuration` method.

#### AppConfig
AppConfig store provider fetches any JSON document from your AppConfig definition with the `get_configuration` method.
You can use it to get more

```python hl_lines="8"
app_config = AppConfigStore(
    environment="test",
    application="powertools",
    name="test_conf_name",
    envelope = "features.feature_flags"
)

app_config.get_configuration()
```


## Testing your code
You can unit test your feature flags locally without any setup in AWS AppConfig.
Because `AppConfigStore` only fetches a JSON document with a specific schema you can mock the response and use it to verify the rule evaluation.
Here is an example how to test a single feature with one rule:

=== "test_feature_flags"
    ```python
    def test_flags_condition_match(mocker):
        expected_value = True
        mocked_app_config_schema = {
            "my_feature": {
                "default": expected_value,
                "rules": {
                    "tenant id equals 345345435": {
                        "when_match": True,
                        "conditions": [
                            {
                                "action": RuleAction.EQUALS.value,
                                "key": "tenant_id",
                                "value": "345345435",
                            }
                        ],
                    }
                },
                }
        }

    feature_flags = init_feature_flags(mocker, mocked_app_config_schema, Config(region_name="us-east-1"))
    toggle = feature_flags.evaluate(name="my_feature", context={"tenant_id": "345345435", "username": "a"}, default=False)
    assert toggle == expected_value
    ```

=== "init_feature_flags"

    ```python
    def init_feature_flags(
        mocker, mock_schema: Dict, config: Config, envelope: str = "", jmespath_options: Optional[Dict] = None
    ) -> FeatureFlags:
        mocked_get_conf = mocker.patch("aws_lambda_powertools.utilities.feature_flags.AppConfigStore.get_configuration")
        mocked_get_conf.return_value = mock_schema

        app_conf_store = AppConfigStore(
            environment="test_env",
            application="test_app",
            name="test_conf_name",
            cache_seconds=600,
            sdk_config=config,
            envelope=envelope,
            jmespath_options=jmespath_options,
        )
        feature_flags: FeatureFlags = FeatureFlags(store=app_conf_fetcher)
        return feature_flags
    ```
