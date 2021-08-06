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

TODO: fix tip

!!! tip "Read [this article](https://martinfowler.com/articles/feature-toggles.html){target="_blank"} for more details
on different types of feature flags and trade-offs"

## Key features

* Define simple feature flags to dynamically decide when to enable a feature
* Fetch one or all feature flags enabled for a given application context
* Bring your own configuration store

## Getting started

### IAM Permissions

Because powertools needs to fetch the configuration from the AppConfig, you need to add `appconfig:GetConfiguration`
action to your function.

### Required resources

TODO: link to appconfig
By default, this utility provides AWS AppConfig as a configuration store. To create a dedicate you can use this
cloudformation template:

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

The `Content` parameter is a json structure of the feature flags and rules.

TODO: add steps to create new version and new deployment for the config


### Use feature flag store


First setup is to setup the `AppConfigStore` based on the AppConfig parameters you have created with the previous
CloudFormation template.

TOOD: provide full example

=== app.py
```python

app_config = AppConfigStore(
    environment="FeatureStore",
    application="product-dev",
    name="features",
    cache_seconds=300
)
feature_flags = FeatureFlags(store=app_config)
ctx = {"username": "lessa", "tier": "premium", "location": "NL"}

has_premium_features: bool = feature_flags.evaluate(name="premium_features",
                                                    context=ctx,
                                                    default=False)
```

=== schema.json
```json

```

### Evaluating a single feature flag


To fetch a single feature, setup the `FeatureFlags` instance and call the `evaluate` method.

```python
feature_flags = FeatureFlags(store=app_config)
ctx = {"username": "lessa", "tier": "premium", "location": "NL"}

has_premium_features: bool = feature_flags.evaluate(name="premium_features",
                                                    context=ctx,
                                                    default=False)
```

The `context` parameter is optional and will be used for rule evaluation. In this case we have the `key` set
as `username` and `value` set to `lessa`. Feature flag schema to match this could look like this:

```json
{
  "premium_features": {
    "default": false,
    "rules": {
      "username is lessa and tier is premium": {
        "when_match": true,
        "conditions": [
          {
            "action": "EQUALS",
            "key": "username",
            "value": "lessa"
          },
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

In cases where you need to get a list of all the features that are enabled you can use `get_enabled_features` method:

```python
feature_flags = Feature****Flags(store=app_config)
ctx = {"username": "lessa", "tier": "premium", "location": "NL"}

all_features: list[str] = feature_flags.get_enabled_features(context=ctx)
```

As a result you will get a list of all the names of the features from your feaute flag configuration. For example if you
have two features with the following configuration and both are evaluated to `true`:

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

The response of `get_enabled_features` will be `["feautre1", "feature2"]`.


### Feature flags schema

When using the feature flags utility powertools expects specific schema stored in your AppConfig configuration which
incldues:

* list of named features
* default value
* set of rules that powertools will evaluate

Each rule should contain:

* value if condition is met
* list of conditions with `action`, `key` and `value` attributes.

Here is small example of a premium feature with a default value `false` and one rule with a condition: if the passed
context equals `{"tier": "premium"}` return true.

```json
{
  "premium_feature": {
    "default": false
  }
}
```

#### Rules

TODO: explain rules here in detail. The rules are evaluated based on conditions which have the structure:

```json
{
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
```

#### Conditions

The `action` configuration can have 4 different values: `EQUALS`, `STARTSWITH`, `ENDSWITH`, `IN`, `NOT_IN`. If you have
multiple rules powertools will evaluate every rule with a logical AND.


## Advanced

### Adjusting in-memory cache

### Envelope (any better name)

### Built-in store provider

#### AppConfig

## Testing your code
