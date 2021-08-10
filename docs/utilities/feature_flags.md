---
title: Feature flags
description: Utility
---

!!! note "This is currently in Beta, as we might change Store parameters in the next release."

The feature flags utility provides a simple rule engine to define when one or multiple features should be enabled depending on the input.

## Terminology

Feature flags are used to modify behaviour without changing the application's code. These flags can be **static** or **dynamic**.

**Static flags**. Indicates something is simply `on` or `off`, for example `TRACER_ENABLED=True`.

**Dynamic flags**. Indicates something can have varying states, for example enable a premium feature for customer X not Y.

!!! tip "You can use [Parameters utility](parameters.md) for static flags while this utility can do both static and dynamic feature flags."

!!! warning "Be mindful that feature flags can increase the complexity of your application over time; use them sparingly."

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

By default, we cache configuration retrieved from the Store for 5 seconds for performance and reliability reasons.

You can override `max_age` parameter when instantiating the store.

```python hl_lines="7"
from aws_lambda_powertools.utilities.feature_flags import FeatureFlags, AppConfigStore

app_config = AppConfigStore(
    environment="dev",
    application="product-catalogue",
    name="features",
    max_age=300
)
```

### Envelope

There are scenarios where you might want to include feature flags as part of an existing application configuration.

For this to work, you need to use a JMESPath expression via the `envelope` parameter to extract that key as the feature flags configuration.

=== "app.py"

	```python hl_lines="7"
	from aws_lambda_powertools.utilities.feature_flags import FeatureFlags, AppConfigStore

	app_config = AppConfigStore(
		environment="dev",
		application="product-catalogue",
		name="configuration",
		envelope = "feature_flags"
	)
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

!!! info "For GA, you'll be able to bring your own store."

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

=== "appconfig_store_example.py"

```python hl_lines="19-25"
from botocore.config import Config

import jmespath

boto_config = Config(read_timeout=10, retries={"total_max_attempts": 2})

# Custom JMESPath functions
class CustomFunctions(jmespath.functions.Functions):

    @jmespath.functions.signature({'types': ['string']})
    def _func_special_decoder(self, s):
        return my_custom_decoder_logic(s)


custom_jmespath_options = {"custom_functions": CustomFunctions()}


app_config = AppConfigStore(
    environment="dev",
    application="product-catalogue",
    name="configuration",
    max_age=120,
    envelope = "features",
    sdk_config=boto_config,
    jmespath_options=custom_jmespath_options
)
```


## Testing your code

You can unit test your feature flags locally and independently without setting up AWS AppConfig.

`AppConfigStore` only fetches a JSON document with a specific schema. This allows you to mock the response and use it to verify the rule evaluation.

!!! warning "This excerpt relies on `pytest` and `pytest-mock` dependencies"

=== "test_feature_flags_independently.py"

    ```python hl_lines="9-11"
	from typing import Dict, List, Optional

	from aws_lambda_powertools.utilities.feature_flags import FeatureFlags, AppConfigStore, RuleAction


	def init_feature_flags(mocker, mock_schema, envelope="") -> FeatureFlags:
		"""Mock AppConfig Store get_configuration method to use mock schema instead"""

		method_to_mock = "aws_lambda_powertools.utilities.feature_flags.AppConfigStore.get_configuration"
		mocked_get_conf = mocker.patch(method_to_mock)
		mocked_get_conf.return_value = mock_schema

		app_conf_store = AppConfigStore(
			environment="test_env",
			application="test_app",
			name="test_conf_name",
			envelope=envelope,
		)

		return FeatureFlags(store=app_conf_store)


	def test_flags_condition_match(mocker):
		# GIVEN
		expected_value = True
		mocked_app_config_schema = {
			"my_feature": {
				"default": expected_value,
				"rules": {
					"tenant id equals 12345": {
						"when_match": True,
						"conditions": [
							{
								"action": RuleAction.EQUALS.value,
								"key": "tenant_id",
								"value": "12345",
							}
						],
					}
				},
				}
		}

		# WHEN
		ctx = {"tenant_id": "12345", "username": "a"}
		feature_flags = init_feature_flags(mocker=mocker, mock_schema=mocked_app_config_schema)
		flag = feature_flags.evaluate(name="my_feature", context=ctx, default=False)

		# THEN
		assert flag == expected_value
    ```
