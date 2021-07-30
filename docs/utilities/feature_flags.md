---
title: Feature flags
description: Utility
---

The feature flags utility provides a simple rule engine to define when one or multiple features should be enabled depending on the input.

!!! tip "For simpler use cases where a feature is simply on or off for all users, use [Parameters](parameters.md) utility instead."

## Terminology

> Explain the difference between static vs dynamic feature flags

## Key features

> TODO: Revisit once getting started and advanced sections are complete

* Define simple feature flags to dynamically decide when to enable a feature
* Fetch one or all feature flags enabled for a given application context
* Bring your own configuration store

## Getting started
### IAM Permissions

This utility requires additional permissions to work as expected.

Provider | Function/Method | IAM Permission
------------------------------------------------- | ------------------------------------------------- | ---------------------------------------------------------------------------------
App Config | `AppConfigProvider.get_app_config`, `get_app_config` | `appconfig:GetConfiguration`

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

## TODO

* Review param names and UX
	- Deep dive on naming - ConfigurationStore vs SchemaFetcher vs Schema
	- How can we make it easier to get started
* Getting started
  	- Sample Infrastructure
  	- Quickest way to start --- defaults, built-ins
* Advanced section
  	- Bring your own

## Changes

Potential changes to be validated when docs are in a better shape

- [ ] `rules_context` to `context`
- [ ] `ConfigurationStore` to `FeatureFlags`
- [ ] `SchemaFetcher` to `StoreProvider`
- [ ] Use `base.py` for interfaces for consistency (e.g. Metrics, Tracer, etc.)
- [ ] Some docstrings and logger refer to AWS AppConfig only (outdated given SchemaFetcher)
- [ ]
