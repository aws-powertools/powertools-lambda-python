---
title: Homepage
description: AWS Lambda Powertools Python
---

A suite of utilities for AWS Lambda functions to ease adopting best practices such as tracing, structured logging, custom metrics, and more.

???+ tip "Tip: Looking for a quick read through how the core features are used?"

    Check out [this detailed blog post](https://aws.amazon.com/blogs/opensource/simplifying-serverless-best-practices-with-lambda-powertools/) with a practical example.

## Tenets

Core utilities such as Tracing, Logging, Metrics, and Event Handler will be available across all Lambda Powertools runtimes. Additional utilities are subjective to each language ecosystem and customer demand.

* **AWS Lambda only**. We optimise for AWS Lambda function environments and supported runtimes only. Utilities might work with web frameworks and non-Lambda environments, though they are not officially supported.
* **Eases the adoption of best practices**. The main priority of the utilities is to facilitate best practices adoption, as defined in the AWS Well-Architected Serverless Lens; all other functionality is optional.
* **Keep it lean**. Additional dependencies are carefully considered for security and ease of maintenance, and prevent negatively impacting startup time.
* **We strive for backwards compatibility**. New features and changes should keep backwards compatibility. If a breaking change cannot be avoided, the deprecation and migration process should be clearly defined.
* **We work backwards from the community**. We aim to strike a balance of what would work best for 80% of customers. Emerging practices are considered and discussed via Requests for Comment (RFCs)
* **Progressive**. Utilities are designed to be incrementally adoptable for customers at any stage of their Serverless journey. They follow language idioms and their community’s common practices.

## Install

Powertools is available in the following formats:

* **Lambda Layer**: [**arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPython:7 :clipboard:**](#){: .copyMe}
* **PyPi**: **`pip install aws-lambda-powertools`**

### Lambda Layer

[Lambda Layer](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html){target="_blank"} is a .zip file archive that can contain additional code, pre-packaged dependencies, data,  or configuration files. Layers promote code sharing and separation of responsibilities so that you can iterate faster on writing business logic.

You can include Lambda Powertools Lambda Layer using [AWS Lambda Console](https://docs.aws.amazon.com/lambda/latest/dg/invocation-layers.html#invocation-layers-using){target="_blank"}, or your preferred deployment framework.

??? note "Note: Expand to copy any regional Lambda Layer ARN"

    | Region | Layer ARN
    |--------------------------- | ---------------------------
    | `us-east-1` | [arn:aws:lambda:us-east-1:017000801446:layer:AWSLambdaPowertoolsPython:7 :clipboard:](#){: .copyMe}
    | `us-east-2` | [arn:aws:lambda:us-east-2:017000801446:layer:AWSLambdaPowertoolsPython:7 :clipboard:](#){: .copyMe}
    | `us-west-1` | [arn:aws:lambda:us-west-1:017000801446:layer:AWSLambdaPowertoolsPython:7 :clipboard:](#){: .copyMe}
    | `us-west-2` | [arn:aws:lambda:us-west-2:017000801446:layer:AWSLambdaPowertoolsPython:7 :clipboard:](#){: .copyMe}
    | `ap-south-1` | [arn:aws:lambda:ap-south-1:017000801446:layer:AWSLambdaPowertoolsPython:7 :clipboard:](#){: .copyMe}
    | `ap-northeast-1` | [arn:aws:lambda:ap-northeast-1:017000801446:layer:AWSLambdaPowertoolsPython:7 :clipboard:](#){: .copyMe}
    | `ap-northeast-2` | [arn:aws:lambda:ap-northeast-2:017000801446:layer:AWSLambdaPowertoolsPython:7 :clipboard:](#){: .copyMe}
    | `ap-northeast-3` | [arn:aws:lambda:ap-northeast-3:017000801446:layer:AWSLambdaPowertoolsPython:7 :clipboard:](#){: .copyMe}
    | `ap-southeast-1` | [arn:aws:lambda:ap-southeast-1:017000801446:layer:AWSLambdaPowertoolsPython:7 :clipboard:](#){: .copyMe}
    | `ap-southeast-2` | [arn:aws:lambda:ap-southeast-2:017000801446:layer:AWSLambdaPowertoolsPython:7 :clipboard:](#){: .copyMe}
    | `eu-central-1` | [arn:aws:lambda:eu-central-1:017000801446:layer:AWSLambdaPowertoolsPython:7 :clipboard:](#){: .copyMe}
    | `eu-west-1` | [arn:aws:lambda:eu-west-1:017000801446:layer:AWSLambdaPowertoolsPython:7 :clipboard:](#){: .copyMe}
    | `eu-west-2` | [arn:aws:lambda:eu-west-2:017000801446:layer:AWSLambdaPowertoolsPython:7 :clipboard:](#){: .copyMe}
    | `eu-west-3` | [arn:aws:lambda:eu-west-3:017000801446:layer:AWSLambdaPowertoolsPython:7 :clipboard:](#){: .copyMe}
    | `eu-north-1` | [arn:aws:lambda:eu-north-1:017000801446:layer:AWSLambdaPowertoolsPython:7 :clipboard:](#){: .copyMe}
    | `ca-central-1` | [arn:aws:lambda:ca-central-1:017000801446:layer:AWSLambdaPowertoolsPython:7 :clipboard:](#){: .copyMe}
    | `sa-east-1` | [arn:aws:lambda:sa-east-1:017000801446:layer:AWSLambdaPowertoolsPython:7 :clipboard:](#){: .copyMe}

=== "SAM"

    ```yaml hl_lines="5"
    MyLambdaFunction:
        Type: AWS::Serverless::Function
        Properties:
            Layers:
                - !Sub arn:aws:lambda:${AWS::Region}:017000801446:layer:AWSLambdaPowertoolsPython:7
    ```

=== "Serverless framework"

    ```yaml hl_lines="5"
	functions:
		hello:
		  handler: lambda_function.lambda_handler
		  layers:
			- arn:aws:lambda:${aws:region}:017000801446:layer:AWSLambdaPowertoolsPython:7
    ```

=== "CDK"

    ```python hl_lines="11 16"
    from aws_cdk import core, aws_lambda

    class SampleApp(core.Construct):

        def __init__(self, scope: core.Construct, id_: str, env: core.Environment) -> None:
            super().__init__(scope, id_)

            powertools_layer = aws_lambda.LayerVersion.from_layer_version_arn(
                self,
                id="lambda-powertools",
                layer_version_arn=f"arn:aws:lambda:{env.region}:017000801446:layer:AWSLambdaPowertoolsPython:7"
            )
            aws_lambda.Function(self,
                'sample-app-lambda',
                runtime=aws_lambda.Runtime.PYTHON_3_9,
                layers=[powertools_layer]
                # other props...
            )
    ```

=== "Terraform"

    ```terraform hl_lines="9 38"
    terraform {
      required_version = "~> 1.0.5"
      required_providers {
        aws = "~> 3.50.0"
      }
    }

    provider "aws" {
      region  = "{region}"
    }

    resource "aws_iam_role" "iam_for_lambda" {
      name = "iam_for_lambda"

      assume_role_policy = <<EOF
        {
          "Version": "2012-10-17",
          "Statement": [
            {
              "Action": "sts:AssumeRole",
              "Principal": {
                "Service": "lambda.amazonaws.com"
              },
              "Effect": "Allow"
            }
          ]
        }
        EOF
	}

    resource "aws_lambda_function" "test_lambda" {
      filename      = "lambda_function_payload.zip"
      function_name = "lambda_function_name"
      role          = aws_iam_role.iam_for_lambda.arn
      handler       = "index.test"
      runtime 		= "python3.9"
      layers 		= ["arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPython:7"]

      source_code_hash = filebase64sha256("lambda_function_payload.zip")
    }


    ```

=== "Amplify"

    ```zsh
    # Create a new one with the layer
    ❯ amplify add function
    ? Select which capability you want to add: Lambda function (serverless function)
    ? Provide an AWS Lambda function name: <NAME-OF-FUNCTION>
    ? Choose the runtime that you want to use: Python
    ? Do you want to configure advanced settings? Yes
    ...
    ? Do you want to enable Lambda layers for this function? Yes
    ? Enter up to 5 existing Lambda layer ARNs (comma-separated): arn:aws:lambda:eu-central-1:017000801446:layer:AWSLambdaPowertoolsPython:7
    ❯ amplify push -y


    # Updating an existing function and add the layer
    ❯ amplify update function
    ? Select the Lambda function you want to update test2
    General information
    - Name: <NAME-OF-FUNCTION>
    ? Which setting do you want to update? Lambda layers configuration
    ? Do you want to enable Lambda layers for this function? Yes
    ? Enter up to 5 existing Lambda layer ARNs (comma-separated): arn:aws:lambda:eu-central-1:017000801446:layer:AWSLambdaPowertoolsPython:7
    ? Do you want to edit the local lambda function now? No
    ```

=== "Get the Layer .zip contents"
	Change {region} to your AWS region, e.g. `eu-west-1`

    ```bash title="AWS CLI"
	aws lambda get-layer-version-by-arn --arn arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPython:7 --region {region}
    ```

    The pre-signed URL to download this Lambda Layer will be within `Location` key.

???+ warning "Warning: Limitations"

	Container Image deployment (OCI) or inline Lambda functions do not support Lambda Layers.

	Lambda Powertools Lambda Layer do not include `pydantic` library - required dependency for the `parser` utility. See [SAR](#sar) option instead.


#### SAR

Serverless Application Repository (SAR) App deploys a CloudFormation stack with a copy of our Lambda Layer in your AWS account and region.

Despite having more steps compared to the [public Layer ARN](#lambda-layer) option, the benefit is that you can specify a semantic version you want to use.

| App | ARN | Description
|----------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------
| [aws-lambda-powertools-python-layer](https://serverlessrepo.aws.amazon.com/applications/eu-west-1/057560766410/aws-lambda-powertools-python-layer) | [arn:aws:serverlessrepo:eu-west-1:057560766410:applications/aws-lambda-powertools-python-layer](#){: .copyMe} :clipboard: | Core dependencies only; sufficient for nearly all utilities.
| [aws-lambda-powertools-python-layer-extras](https://serverlessrepo.aws.amazon.com/applications/eu-west-1/057560766410/aws-lambda-powertools-python-layer-extras) | [arn:aws:serverlessrepo:eu-west-1:057560766410:applications/aws-lambda-powertools-python-layer-extras](#){: .copyMe} :clipboard: | Core plus extra dependencies such as `pydantic` that is required by `parser` utility.

???+ warning
    **Layer-extras** does not support Python 3.6 runtime. This layer also includes all extra dependencies: `22.4MB zipped`, `~155MB unzipped`.

???+ tip
	You can create a shared Lambda Layers stack and make this along with other account level layers stack.


If using SAM, you can include this SAR App as part of your shared Layers stack, and lock to a specific semantic version. Once deployed, it'll be available across the account this is deployed to.

=== "SAM"

    ```yaml hl_lines="5-6 12-13"
    AwsLambdaPowertoolsPythonLayer:
        Type: AWS::Serverless::Application
        Properties:
            Location:
                ApplicationId: arn:aws:serverlessrepo:eu-west-1:057560766410:applications/aws-lambda-powertools-python-layer
                SemanticVersion: 1.24.0 # change to latest semantic version available in SAR

    MyLambdaFunction:
        Type: AWS::Serverless::Function
        Properties:
            Layers:
                # fetch Layer ARN from SAR App stack output
                - !GetAtt AwsLambdaPowertoolsPythonLayer.Outputs.LayerVersionArn
    ```

=== "Serverless framework"

    ```yaml hl_lines="5 8 10-11"
    functions:
        main:
        handler: lambda_function.lambda_handler
        layers:
            - !GetAtt AwsLambdaPowertoolsPythonLayer.Outputs.LayerVersionArn

    resources:
        Transform: AWS::Serverless-2016-10-31
        Resources:****
        AwsLambdaPowertoolsPythonLayer:
            Type: AWS::Serverless::Application
            Properties:
                Location:
                    ApplicationId: arn:aws:serverlessrepo:eu-west-1:057560766410:applications/aws-lambda-powertools-python-layer
                    # Find latest from github.com/awslabs/aws-lambda-powertools-python/releases
                    SemanticVersion: 1.24.0
    ```

=== "CDK"

    ```python hl_lines="14 22-23 31"
    from aws_cdk import core, aws_sam as sam, aws_lambda

    POWERTOOLS_BASE_NAME = 'AWSLambdaPowertools'
    # Find latest from github.com/awslabs/aws-lambda-powertools-python/releases
    POWERTOOLS_VER = '1.23.0'
    POWERTOOLS_ARN = 'arn:aws:serverlessrepo:eu-west-1:057560766410:applications/aws-lambda-powertools-python-layer'

    class SampleApp(core.Construct):

        def __init__(self, scope: core.Construct, id_: str) -> None:
            super().__init__(scope, id_)

            # Launches SAR App as CloudFormation nested stack and return Lambda Layer
            powertools_app = sam.CfnApplication(self,
                f'{POWERTOOLS_BASE_NAME}Application',
                location={
                    'applicationId': POWERTOOLS_ARN,
                    'semanticVersion': POWERTOOLS_VER
                },
            )

            powertools_layer_arn = powertools_app.get_att("Outputs.LayerVersionArn").to_string()
            powertools_layer_version = aws_lambda.LayerVersion.from_layer_version_arn(self, f'{POWERTOOLS_BASE_NAME}', powertools_layer_arn)

            aws_lambda.Function(self,
                'sample-app-lambda',
                runtime=aws_lambda.Runtime.PYTHON_3_8,
                function_name='sample-lambda',
                code=aws_lambda.Code.asset('./src'),
                handler='app.handler',
                layers: [powertools_layer_version]
            )
    ```

=== "Terraform"

	> Credits to [Dani Comnea](https://github.com/DanyC97) for providing the Terraform equivalent.

    ```terraform hl_lines="12-13 15-20 23-25 40"
    terraform {
      required_version = "~> 0.13"
      required_providers {
        aws = "~> 3.50.0"
      }
    }

    provider "aws" {
      region  = "us-east-1"
    }

    resource "aws_serverlessapplicationrepository_cloudformation_stack" "deploy_sar_stack" {
      name = "aws-lambda-powertools-python-layer"

      application_id   = data.aws_serverlessapplicationrepository_application.sar_app.application_id
      semantic_version = data.aws_serverlessapplicationrepository_application.sar_app.semantic_version
      capabilities = [
        "CAPABILITY_IAM",
        "CAPABILITY_NAMED_IAM"
      ]
    }

    data "aws_serverlessapplicationrepository_application" "sar_app" {
      application_id   = "arn:aws:serverlessrepo:eu-west-1:057560766410:applications/aws-lambda-powertools-python-layer"
      semantic_version = var.aws_powertools_version
    }

    variable "aws_powertools_version" {
      type        = string
      default     = "1.20.2"
      description = "The AWS Powertools release version"
    }

    output "deployed_powertools_sar_version" {
      value = data.aws_serverlessapplicationrepository_application.sar_app.semantic_version
    }

	# Fetch Lambda Powertools Layer ARN from deployed SAR App
	output "aws_lambda_powertools_layer_arn" {
	  value = aws_serverlessapplicationrepository_cloudformation_stack.deploy_sar_stack.outputs.LayerVersionArn
	}
    ```

??? example "Example: Least-privileged IAM permissions to deploy Layer"

    > Credits to [mwarkentin](https://github.com/mwarkentin) for providing the scoped down IAM permissions.

    The region and the account id for `CloudFormationTransform` and `GetCfnTemplate` are fixed.

    === "template.yml"

        ```yaml hl_lines="21-52"
        AWSTemplateFormatVersion: "2010-09-09"
        Resources:
            PowertoolsLayerIamRole:
            Type: "AWS::IAM::Role"
            Properties:
                AssumeRolePolicyDocument:
                Version: "2012-10-17"
                Statement:
                    - Effect: "Allow"
                    Principal:
                        Service:
                        - "cloudformation.amazonaws.com"
                    Action:
                        - "sts:AssumeRole"
                Path: "/"
            PowertoolsLayerIamPolicy:
            Type: "AWS::IAM::Policy"
            Properties:
                PolicyName: PowertoolsLambdaLayerPolicy
                PolicyDocument:
                Version: "2012-10-17"
                Statement:
                    - Sid: CloudFormationTransform
                    Effect: Allow
                    Action: cloudformation:CreateChangeSet
                    Resource:
                        - arn:aws:cloudformation:us-east-1:aws:transform/Serverless-2016-10-31
                    - Sid: GetCfnTemplate
                    Effect: Allow
                    Action:
                        - serverlessrepo:CreateCloudFormationTemplate
                        - serverlessrepo:GetCloudFormationTemplate
                    Resource:
                        # this is arn of the powertools SAR app
                        - arn:aws:serverlessrepo:eu-west-1:057560766410:applications/aws-lambda-powertools-python-layer
                    - Sid: S3AccessLayer
                    Effect: Allow
                    Action:
                        - s3:GetObject
                    Resource:
                        # AWS publishes to an external S3 bucket locked down to your account ID
                        # The below example is us publishing lambda powertools
                        # Bucket: awsserverlessrepo-changesets-plntc6bfnfj
                        # Key: *****/arn:aws:serverlessrepo:eu-west-1:057560766410:applications-aws-lambda-powertools-python-layer-versions-1.10.2/aeeccf50-****-****-****-*********
                        - arn:aws:s3:::awsserverlessrepo-changesets-*/*
                    - Sid: GetLayerVersion
                    Effect: Allow
                    Action:
                        - lambda:PublishLayerVersion
                        - lambda:GetLayerVersion
                    Resource:
                        - !Sub arn:aws:lambda:${AWS::Region}:${AWS::AccountId}:layer:aws-lambda-powertools-python-layer*
                Roles:
                - Ref: "PowertoolsLayerIamRole"
        ```

You can fetch available versions via SAR ListApplicationVersions API:

```bash title="AWS CLI example"
aws serverlessrepo list-application-versions \
	--application-id arn:aws:serverlessrepo:eu-west-1:057560766410:applications/aws-lambda-powertools-python-layer
```

## Quick getting started

```bash title="Hello world example using SAM CLI"
sam init --location https://github.com/aws-samples/cookiecutter-aws-sam-python
```

## Features

| Utility | Description
| ------------------------------------------------- | ---------------------------------------------------------------------------------
[Tracing](./core/tracer.md) | Decorators and utilities to trace Lambda function handlers, and both synchronous and asynchronous functions
[Logger](./core/logger.md) | Structured logging made easier, and decorator to enrich structured logging with key Lambda context details
[Metrics](./core/metrics.md) | Custom Metrics created asynchronously via CloudWatch Embedded Metric Format (EMF)
[Event handler: AppSync](./core/event_handler/appsync.md) | AppSync event handler for Lambda Direct Resolver and Amplify GraphQL Transformer function
[Event handler: API Gateway and ALB](https://awslabs.github.io/aws-lambda-powertools-python/latest/core/event_handler/api_gateway/) | Amazon API Gateway REST/HTTP API and ALB event handler for Lambda functions invoked using Proxy integration
[Middleware factory](./utilities/middleware_factory.md) | Decorator factory to create your own middleware to run logic before, and after each Lambda invocation
[Parameters](./utilities/parameters.md) | Retrieve parameter values from AWS Systems Manager Parameter Store, AWS Secrets Manager, or Amazon DynamoDB, and cache them for a specific amount of time
[Batch processing](./utilities/batch.md) | Handle partial failures for AWS SQS batch processing
[Typing](./utilities/typing.md) | Static typing classes to speedup development in your IDE
[Validation](./utilities/validation.md) | JSON Schema validator for inbound events and responses
[Event source data classes](./utilities/data_classes.md) | Data classes describing the schema of common Lambda event triggers
[Parser](./utilities/parser.md) | Data parsing and deep validation using Pydantic
[Idempotency](./utilities/idempotency.md) | Idempotent Lambda handler
[Feature Flags](./utilities/feature_flags.md) | A simple rule engine to evaluate when one or multiple features should be enabled depending on the input

## Environment variables

???+ info
	Explicit parameters take precedence over environment variables

| Environment variable | Description | Utility | Default |
| ------------------------------------------------- | --------------------------------------------------------------------------------- | --------------------------------------------------------------------------------- | ------------------------------------------------- |
| **POWERTOOLS_SERVICE_NAME** | Sets service name used for tracing namespace, metrics dimension and structured logging | All | `"service_undefined"` |
| **POWERTOOLS_METRICS_NAMESPACE** | Sets namespace used for metrics | [Metrics](./core/metrics) | `None` |
| **POWERTOOLS_TRACE_DISABLED** | Explicitly disables tracing | [Tracing](./core/tracer) | `false` |
| **POWERTOOLS_TRACER_CAPTURE_RESPONSE** | Captures Lambda or method return as metadata. | [Tracing](./core/tracer) | `true` |
| **POWERTOOLS_TRACER_CAPTURE_ERROR** | Captures Lambda or method exception as metadata. | [Tracing](./core/tracer) | `true` |
| **POWERTOOLS_TRACE_MIDDLEWARES** | Creates sub-segment for each custom middleware | [Middleware factory](./utilities/middleware_factory) | `false` |
| **POWERTOOLS_LOGGER_LOG_EVENT** | Logs incoming event | [Logging](./core/logger) | `false` |
| **POWERTOOLS_LOGGER_SAMPLE_RATE** | Debug log sampling | [Logging](./core/logger) | `0` |
| **POWERTOOLS_LOG_DEDUPLICATION_DISABLED** | Disables log deduplication filter protection to use Pytest Live Log feature | [Logging](./core/logger) | `false` |
| **POWERTOOLS_EVENT_HANDLER_DEBUG** | Enables debugging mode for event handler  | [Event Handler](./core/event_handler/api_gateway.md#debug-mode) | `false` |
| **LOG_LEVEL** | Sets logging level | [Logging](./core/logger) | `INFO` |

## Debug mode

As a best practice, AWS Lambda Powertools module logging statements are suppressed. If necessary, you can enable debugging using `set_package_logger` for additional information on every internal operation:

```python title="Powertools debug mode example"
from aws_lambda_powertools.logging.logger import set_package_logger

set_package_logger()
```
