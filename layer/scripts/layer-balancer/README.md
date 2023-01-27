<!-- markdownlint-disable MD041 MD043 -->
# Layer balancer

This folder contains a Go project that balances the layer version of Lambda Powertools across all regions, so
every region has the same layer version.

Before:

```text
arn:aws:lambda:eu-central-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:11
...
arn:aws:lambda:eu-west-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:9
```

After:

```text
arn:aws:lambda:eu-central-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:11
...
arn:aws:lambda:eu-west-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:11
```

## What's happening under the hood?

1. Query all regions to find the greatest version number
2. Download the latest layer from eu-central-1
3. Use the layer contents to bump the version on each region until it matches 1

## Requirements

* go >= 1.18

## How to use

1. Set your AWS_PROFILE to the correct profile
2. `go run .`
3. Profit :-)
