---
title: Feature flags
description: Utility
---

The feature flags utility provides a simple rule engine to define when one or multiple features should be enabled depending on the input.

!!! tip "For simpler use cases where a feature is simply on or off for all users, use [Parameters](parameters.md) utility instead."

## Terminology

Feature flags are used to modify a system behaviour without having to change their code. These flags can be static or dynamic.

**Static feature flags** are commonly used for long-lived behaviours that will rarely change, for example `TRACER_ENABLED=True`. These are better suited for [Parameters utility](parameters.md).

**Dynamic feature flags** are typically used for experiments where you'd want to enable a feature for a limited set of customers, for example A/B testing and Canary releases. These are better suited for this utility, as you can create multiple conditions on whether a feature flag should be `True` or `False`.

That being said, be mindful that feature flags can increase your application complexity over time if you're not careful; use them sparingly.

!!! tip "Read [this article](https://martinfowler.com/articles/feature-toggles.html){target="_blank"} for more details on different types of feature flags and trade-offs"

## Key features

> TODO: Revisit once getting started and advanced sections are complete

* Define simple feature flags to dynamically decide when to enable a feature
* Fetch one or all feature flags enabled for a given application context
* Bring your own configuration store

## Getting started
### IAM Permissions

By default, this utility provides AWS AppConfig as a configuration store. As such, you IAM Role needs permission - `appconfig:GetConfiguration` - to fetch feature flags from AppConfig.

### Creating feature flags

> NOTE: Explain schema, provide sample boto3 script and CFN to create one

#### Rules



### Fetching a single feature flag

### Fetching all feature flags

### Advanced

#### Adjusting cache TTL

### Partially enabling features

### Bring your own store provider

## Testing your code

> NOTE: Share example on how customers can unit test their feature flags

## Changes

Potential changes to be validated when docs are in a better shape

- [x] ~~`rules_context` to `context`~~
- [x] `ConfigurationStore` to `FeatureFlags`
- [x] `StoreProvider` to `StoreProvider`
- [ ] Use `base.py` for interfaces for consistency (e.g. Metrics, Tracer, etc.)
- [ ] Some docstrings and logger refer to AWS AppConfig only (outdated given StoreProvider)
- [ ] Review why we're testing a private method(`is_rule_matched`)
- [x] AppConfig construct parameter names for consistency (e.g. `configuration_name` -> `name`, `service` -> `application`)
- [ ] Review `get_configuration`, `get_json_configuration`
- [ ] Review `get_feature` in favour of `get_feature_toggle`
