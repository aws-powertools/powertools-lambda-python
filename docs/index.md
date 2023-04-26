---
title: Homepage
description: AWS Lambda Powertools for Python
---

<!-- markdownlint-disable MD043 MD013 -->

Powertools is a developer toolkit to implement Serverless best practices and increase developer velocity.

???+ tip
    Powertools is also available for [Java](https://awslabs.github.io/aws-lambda-powertools-java/){target="_blank"}, [TypeScript](https://awslabs.github.io/aws-lambda-powertools-typescript/latest/){target="_blank"}, and [.NET](https://awslabs.github.io/aws-lambda-powertools-dotnet/){target="_blank"}

??? hint "Support this project by becoming a reference customer, sharing your work, or using Layers/SAR :heart:"

    You can choose to support us in three ways:

    1) [**Become a reference customer**](https://github.com/awslabs/aws-lambda-powertools-python/issues/new?assignees=&labels=customer-reference&template=support_powertools.yml&title=%5BSupport+Lambda+Powertools%5D%3A+%3Cyour+organization+name%3E). This gives us permission to list your company in our documentation.

    2) [**Share your work**](https://github.com/awslabs/aws-lambda-powertools-python/issues/new?assignees=&labels=community-content&template=share_your_work.yml&title=%5BI+Made+This%5D%3A+%3CTITLE%3E). Blog posts, video, sample projects you used Powertools!

    3) Use [**Lambda Layers**](#lambda-layer) or [**SAR**](#sar), if possible. This helps us understand who uses Powertools in a non-intrusive way, and helps us gain future investments for other Powertools languages.

    When using Layers, you can add Powertools as a dev dependency (or as part of your virtual env) to not impact the development process.

## Install

You can install Powertools using one of the following options:

* **Lambda Layer (x86_64)**: [**arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV2:31**](#){: .copyMe}:clipboard:
* **Lambda Layer (arm64)**: [**arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:31**](#){: .copyMe}:clipboard:
* **Pip**: **[`pip install "aws-lambda-powertools"`](#){: .copyMe}:clipboard:**

??? question "Using Pip? You might need to install additional dependencies."
    [**Tracer**](./core/tracer.md){target="_blank"}, [**Validation**](./utilities/validation.md){target="_blank"} and [**Parser**](./utilities/parser.md){target="_blank"} require additional dependencies. If you prefer to install all of them, use [**`pip install "aws-lambda-powertools[all]"`**](#){: .copyMe}:clipboard:.

    For example:

    * **Tracer**: **[`pip install "aws-lambda-powertools[tracer]"`](#){: .copyMe}:clipboard:**
    * **Validation**: **[`pip install "aws-lambda-powertools[validation]"`](#){: .copyMe}:clipboard:**
    * **Parser**: **[`pip install "aws-lambda-powertools[parser]"`](#){: .copyMe}:clipboard:**
    * **Tracer** and **Parser**: **[`pip install "aws-lambda-powertools[tracer,parser]"`](#){: .copyMe}:clipboard:**

### Local development

!!! info "Using Powertools via Lambda Layer? Simply add [**`"aws-lambda-powertools[all]"`**](#){: .copyMe}:clipboard: as a development dependency."

Powertools relies on the [AWS SDK bundled in the Lambda runtime](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html){target="_blank"}. This helps us achieve an optimal package size and initialization. However, when developing locally, you need to install AWS SDK as a development dependency (not as a production dependency):

* **Pip**: [**`pip install "aws-lambda-powertools[aws-sdk]"`**](#){: .copyMe}:clipboard:
* **Poetry**: [**`poetry add "aws-lambda-powertools[aws-sdk]" --group dev`**](#){: .copyMe}:clipboard:
* **Pipenv**: [**`pipenv install --dev "aws-lambda-powertools[aws-sdk]"`**](#){: .copyMe}:clipboard:

??? question "Why is that necessary?"
      Powertools relies on the AWS SDK being available to use in the target runtime (AWS Lambda).

      As a result, it affects your favorite IDE in terms of code auto-completion, or running your tests suite locally with no Lambda emulation such as [AWS SAM CLI](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html){target="_blank"}.

**A word about dependency resolution**

In this context, `[aws-sdk]` is an alias to the `boto3` package. Due to dependency resolution, it'll either install:

* **(A)** the SDK version available in [Lambda runtime](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html){target="_blank"}
* **(B)** a more up-to-date version if another package you use also depends on `boto3`, for example [Powertools Tracer](core/tracer.md){target="_blank"}

### Lambda Layer

???+ warning "As of now, Container Image deployment (OCI) or inline Lambda functions do not support Lambda Layers."

[Lambda Layer](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html){target="_blank"} is a .zip file archive that can contain additional code, pre-packaged dependencies, data,  or configuration files. Layers promote code sharing and separation of responsibilities so that you can iterate faster on writing business logic.

For our Layers, we compile and optimize [all dependencies](https://github.com/awslabs/aws-lambda-powertools-python/blob/develop/pyproject.toml#L98){target="_blank"}, and [remove duplicate dependencies already available in the Lambda runtime](https://github.com/awslabs/cdk-aws-lambda-powertools-layer/blob/main/layer/Python/Dockerfile#L36){target="_blank"} to achieve the most optimal size.

You can include Powertools Lambda Layer using [AWS Lambda Console](https://docs.aws.amazon.com/lambda/latest/dg/invocation-layers.html#invocation-layers-using){target="_blank"}, or your preferred deployment framework.

??? note "Note: Click to expand and copy any regional Lambda Layer ARN"

    === "x86_64"

        | Region           | Layer ARN                                                                                                  |
        | ---------------- | ---------------------------------------------------------------------------------------------------------- |
        | `af-south-1`     | [arn:aws:lambda:af-south-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:31](#){: .copyMe}:clipboard:     |
        | `ap-east-1`      | [arn:aws:lambda:ap-east-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:31](#){: .copyMe}:clipboard:      |
        | `ap-northeast-1` | [arn:aws:lambda:ap-northeast-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:31](#){: .copyMe}:clipboard: |
        | `ap-northeast-2` | [arn:aws:lambda:ap-northeast-2:017000801446:layer:AWSLambdaPowertoolsPythonV2:31](#){: .copyMe}:clipboard: |
        | `ap-northeast-3` | [arn:aws:lambda:ap-northeast-3:017000801446:layer:AWSLambdaPowertoolsPythonV2:31](#){: .copyMe}:clipboard: |
        | `ap-south-1`     | [arn:aws:lambda:ap-south-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:31](#){: .copyMe}:clipboard:     |
        | `ap-south-2`     | [arn:aws:lambda:ap-south-2:017000801446:layer:AWSLambdaPowertoolsPythonV2:31](#){: .copyMe}:clipboard:     |
        | `ap-southeast-1` | [arn:aws:lambda:ap-southeast-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:31](#){: .copyMe}:clipboard: |
        | `ap-southeast-2` | [arn:aws:lambda:ap-southeast-2:017000801446:layer:AWSLambdaPowertoolsPythonV2:31](#){: .copyMe}:clipboard: |
        | `ap-southeast-3` | [arn:aws:lambda:ap-southeast-3:017000801446:layer:AWSLambdaPowertoolsPythonV2:31](#){: .copyMe}:clipboard: |
        | `ap-southeast-4` | [arn:aws:lambda:ap-southeast-4:017000801446:layer:AWSLambdaPowertoolsPythonV2:31](#){: .copyMe}:clipboard: |
        | `ca-central-1`   | [arn:aws:lambda:ca-central-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:31](#){: .copyMe}:clipboard:   |
        | `eu-central-1`   | [arn:aws:lambda:eu-central-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:31](#){: .copyMe}:clipboard:   |
        | `eu-central-2`   | [arn:aws:lambda:eu-central-2:017000801446:layer:AWSLambdaPowertoolsPythonV2:31](#){: .copyMe}:clipboard:   |
        | `eu-north-1`     | [arn:aws:lambda:eu-north-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:31](#){: .copyMe}:clipboard:     |
        | `eu-south-1`     | [arn:aws:lambda:eu-south-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:31](#){: .copyMe}:clipboard:     |
        | `eu-south-2`     | [arn:aws:lambda:eu-south-2:017000801446:layer:AWSLambdaPowertoolsPythonV2:31](#){: .copyMe}:clipboard:     |
        | `eu-west-1`      | [arn:aws:lambda:eu-west-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:31](#){: .copyMe}:clipboard:      |
        | `eu-west-2`      | [arn:aws:lambda:eu-west-2:017000801446:layer:AWSLambdaPowertoolsPythonV2:31](#){: .copyMe}:clipboard:      |
        | `eu-west-3`      | [arn:aws:lambda:eu-west-3:017000801446:layer:AWSLambdaPowertoolsPythonV2:31](#){: .copyMe}:clipboard:      |
        | `me-central-1`   | [arn:aws:lambda:me-central-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:31](#){: .copyMe}:clipboard:   |
        | `me-south-1`     | [arn:aws:lambda:me-south-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:31](#){: .copyMe}:clipboard:     |
        | `sa-east-1`      | [arn:aws:lambda:sa-east-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:31](#){: .copyMe}:clipboard:      |
        | `us-east-1`      | [arn:aws:lambda:us-east-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:31](#){: .copyMe}:clipboard:      |
        | `us-east-2`      | [arn:aws:lambda:us-east-2:017000801446:layer:AWSLambdaPowertoolsPythonV2:31](#){: .copyMe}:clipboard:      |
        | `us-west-1`      | [arn:aws:lambda:us-west-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:31](#){: .copyMe}:clipboard:      |
        | `us-west-2`      | [arn:aws:lambda:us-west-2:017000801446:layer:AWSLambdaPowertoolsPythonV2:31](#){: .copyMe}:clipboard:      |

    === "arm64"

        | Region           | Layer ARN                                                                                                        |
        | ---------------- | ---------------------------------------------------------------------------------------------------------------- |
        | `af-south-1`     | [arn:aws:lambda:af-south-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:31](#){: .copyMe}:clipboard:     |
        | `ap-east-1`      | [arn:aws:lambda:ap-east-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:31](#){: .copyMe}:clipboard:      |
        | `ap-northeast-1` | [arn:aws:lambda:ap-northeast-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:31](#){: .copyMe}:clipboard: |
        | `ap-northeast-2` | [arn:aws:lambda:ap-northeast-2:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:31](#){: .copyMe}:clipboard: |
        | `ap-northeast-3` | [arn:aws:lambda:ap-northeast-3:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:31](#){: .copyMe}:clipboard: |
        | `ap-south-1`     | [arn:aws:lambda:ap-south-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:31](#){: .copyMe}:clipboard:     |
        | `ap-southeast-1` | [arn:aws:lambda:ap-southeast-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:31](#){: .copyMe}:clipboard: |
        | `ap-southeast-2` | [arn:aws:lambda:ap-southeast-2:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:31](#){: .copyMe}:clipboard: |
        | `ap-southeast-3` | [arn:aws:lambda:ap-southeast-3:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:31](#){: .copyMe}:clipboard: |
        | `ca-central-1`   | [arn:aws:lambda:ca-central-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:31](#){: .copyMe}:clipboard:   |
        | `eu-central-1`   | [arn:aws:lambda:eu-central-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:31](#){: .copyMe}:clipboard:   |
        | `eu-north-1`     | [arn:aws:lambda:eu-north-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:31](#){: .copyMe}:clipboard:     |
        | `eu-south-1`     | [arn:aws:lambda:eu-south-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:31](#){: .copyMe}:clipboard:     |
        | `eu-west-1`      | [arn:aws:lambda:eu-west-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:31](#){: .copyMe}:clipboard:      |
        | `eu-west-2`      | [arn:aws:lambda:eu-west-2:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:31](#){: .copyMe}:clipboard:      |
        | `eu-west-3`      | [arn:aws:lambda:eu-west-3:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:31](#){: .copyMe}:clipboard:      |
        | `me-south-1`     | [arn:aws:lambda:me-south-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:31](#){: .copyMe}:clipboard:     |
        | `sa-east-1`      | [arn:aws:lambda:sa-east-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:31](#){: .copyMe}:clipboard:      |
        | `us-east-1`      | [arn:aws:lambda:us-east-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:31](#){: .copyMe}:clipboard:      |
        | `us-east-2`      | [arn:aws:lambda:us-east-2:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:31](#){: .copyMe}:clipboard:      |
        | `us-west-1`      | [arn:aws:lambda:us-west-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:31](#){: .copyMe}:clipboard:      |
        | `us-west-2`      | [arn:aws:lambda:us-west-2:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:31](#){: .copyMe}:clipboard:      |

??? note "Note: Click to expand and copy code snippets for popular frameworks"

    === "x86_64"

        === "SAM"

            ```yaml hl_lines="5"
            MyLambdaFunction:
                Type: AWS::Serverless::Function
                Properties:
                    Layers:
                        - !Sub arn:aws:lambda:${AWS::Region}:017000801446:layer:AWSLambdaPowertoolsPythonV2:31
            ```

        === "Serverless framework"

            ```yaml hl_lines="5"
        	functions:
        		hello:
        		  handler: lambda_function.lambda_handler
        		  layers:
        			- arn:aws:lambda:${aws:region}:017000801446:layer:AWSLambdaPowertoolsPythonV2:31
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
                        layer_version_arn=f"arn:aws:lambda:{env.region}:017000801446:layer:AWSLambdaPowertoolsPythonV2:31"
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
              layers 		= ["arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV2:31"]

              source_code_hash = filebase64sha256("lambda_function_payload.zip")
            }
            ```

        === "Pulumi"

            ```python
            import json
            import pulumi
            import pulumi_aws as aws

            role = aws.iam.Role("role",
                assume_role_policy=json.dumps({
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
                }),
                managed_policy_arns=[aws.iam.ManagedPolicy.AWS_LAMBDA_BASIC_EXECUTION_ROLE]
            )

            lambda_function = aws.lambda_.Function("function",
                layers=[pulumi.Output.concat("arn:aws:lambda:",aws.get_region_output().name,":017000801446:layer:AWSLambdaPowertoolsPythonV2:11")],
                tracing_config={
                    "mode": "Active"
                },
                runtime=aws.lambda_.Runtime.PYTHON3D9,
                handler="index.handler",
                role=role.arn,
                architectures=["x86_64"],
                code=pulumi.FileArchive("lambda_function_payload.zip")
            )
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
            ? Enter up to 5 existing Lambda layer ARNs (comma-separated): arn:aws:lambda:eu-central-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:31
            ❯ amplify push -y


            # Updating an existing function and add the layer
            ❯ amplify update function
            ? Select the Lambda function you want to update test2
            General information
            - Name: <NAME-OF-FUNCTION>
            ? Which setting do you want to update? Lambda layers configuration
            ? Do you want to enable Lambda layers for this function? Yes
            ? Enter up to 5 existing Lambda layer ARNs (comma-separated): arn:aws:lambda:eu-central-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:31
            ? Do you want to edit the local lambda function now? No
            ```

    === "arm64"

        === "SAM"

            ```yaml hl_lines="6"
            MyLambdaFunction:
                Type: AWS::Serverless::Function
                Properties:
                    Architectures: [arm64]
                    Layers:
                        - !Sub arn:aws:lambda:${AWS::Region}:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:31
            ```

        === "Serverless framework"

            ```yaml hl_lines="6"
        	functions:
        		hello:
        		    handler: lambda_function.lambda_handler
                    architecture: arm64
        		    layers:
        		  	- arn:aws:lambda:${aws:region}:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:31
            ```

        === "CDK"

            ```python hl_lines="11 17"
            from aws_cdk import core, aws_lambda

            class SampleApp(core.Construct):

                def __init__(self, scope: core.Construct, id_: str, env: core.Environment) -> None:
                    super().__init__(scope, id_)

                    powertools_layer = aws_lambda.LayerVersion.from_layer_version_arn(
                        self,
                        id="lambda-powertools",
                        layer_version_arn=f"arn:aws:lambda:{env.region}:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:31"
                    )
                    aws_lambda.Function(self,
                        'sample-app-lambda',
                        runtime=aws_lambda.Runtime.PYTHON_3_9,
                        architecture=aws_lambda.Architecture.ARM_64,
                        layers=[powertools_layer]
                        # other props...
                    )
            ```

        === "Terraform"

            ```terraform hl_lines="9 37"
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
              layers 		= ["arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:31"]
              architectures = ["arm64"]

              source_code_hash = filebase64sha256("lambda_function_payload.zip")
            }


            ```

        === "Pulumi"

            ```python
            import json
            import pulumi
            import pulumi_aws as aws

            role = aws.iam.Role("role",
                assume_role_policy=json.dumps({
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
                }),
                managed_policy_arns=[aws.iam.ManagedPolicy.AWS_LAMBDA_BASIC_EXECUTION_ROLE]
            )

            lambda_function = aws.lambda_.Function("function",
                layers=[pulumi.Output.concat("arn:aws:lambda:",aws.get_region_output().name,":017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:11")],
                tracing_config={
                    "mode": "Active"
                },
                runtime=aws.lambda_.Runtime.PYTHON3D9,
                handler="index.handler",
                role=role.arn,
                architectures=["arm64"],
                code=pulumi.FileArchive("lambda_function_payload.zip")
            )
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
            ? Enter up to 5 existing Lambda layer ARNs (comma-separated): arn:aws:lambda:eu-central-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:31
            ❯ amplify push -y


            # Updating an existing function and add the layer
            ❯ amplify update function
            ? Select the Lambda function you want to update test2
            General information
            - Name: <NAME-OF-FUNCTION>
            ? Which setting do you want to update? Lambda layers configuration
            ? Do you want to enable Lambda layers for this function? Yes
            ? Enter up to 5 existing Lambda layer ARNs (comma-separated): arn:aws:lambda:eu-central-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:31
            ? Do you want to edit the local lambda function now? No
            ```

??? question "Want to inspect the contents of the Layer?"
	Change {region} to your AWS region, e.g. `eu-west-1`

    ```bash title="AWS CLI"
    aws lambda get-layer-version-by-arn --arn arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV2:31 --region {region}
    ```

    The pre-signed URL to download this Lambda Layer will be within `Location` key.

#### SAR

Serverless Application Repository (SAR) App deploys a CloudFormation stack with a copy of our Lambda Layer in your AWS account and region.

Compared with the [public Layer ARN](#lambda-layer) option, SAR allows you to choose a semantic version and deploys a Layer in your target account.

| App                                                                                                                                                            | ARN                                                                                                                            | Description                                                           |
| -------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------- |
| [aws-lambda-powertools-python-layer](https://serverlessrepo.aws.amazon.com/applications/eu-west-1/057560766410/aws-lambda-powertools-python-layer)             | [arn:aws:serverlessrepo:eu-west-1:057560766410:applications/aws-lambda-powertools-python-layer](#){: .copyMe}:clipboard:       | Contains all extra dependencies (e.g: pydantic).                      |
| [aws-lambda-powertools-python-layer-arm64](https://serverlessrepo.aws.amazon.com/applications/eu-west-1/057560766410/aws-lambda-powertools-python-layer-arm64) | [arn:aws:serverlessrepo:eu-west-1:057560766410:applications/aws-lambda-powertools-python-layer-arm64](#){: .copyMe}:clipboard: | Contains all extra dependencies (e.g: pydantic). For arm64 functions. |

??? note "Click to expand and copy SAR code snippets for popular frameworks"

    You can create a shared Lambda Layers stack and make this along with other account level layers stack.

    === "SAM"

        ```yaml hl_lines="5-6 12-13"
        AwsLambdaPowertoolsPythonLayer:
            Type: AWS::Serverless::Application
            Properties:
                Location:
                    ApplicationId: arn:aws:serverlessrepo:eu-west-1:057560766410:applications/aws-lambda-powertools-python-layer
                    SemanticVersion: 2.0.0 # change to latest semantic version available in SAR

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
                        SemanticVersion: 2.0.0
        ```

    === "CDK"

        ```python hl_lines="14 22-23 31"
        from aws_cdk import core, aws_sam as sam, aws_lambda

        POWERTOOLS_BASE_NAME = 'AWSLambdaPowertools'
        # Find latest from github.com/awslabs/aws-lambda-powertools-python/releases
        POWERTOOLS_VER = '2.0.0'
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
          default     = "2.0.0"
          description = "The AWS Powertools release version"
        }

        output "deployed_powertools_sar_version" {
          value = data.aws_serverlessapplicationrepository_application.sar_app.semantic_version
        }

    	# Fetch Powertools Layer ARN from deployed SAR App
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

??? note "Click to expand and copy an AWS CLI command to list all versions available in SAR"

    You can fetch available versions via SAR ListApplicationVersions API:

    ```bash title="AWS CLI example"
    aws serverlessrepo list-application-versions \
    	--application-id arn:aws:serverlessrepo:eu-west-1:057560766410:applications/aws-lambda-powertools-python-layer
    ```

## Quick getting started

```bash title="Hello world example using SAM CLI"
sam init --app-template hello-world-powertools-python --name sam-app --package-type Zip --runtime python3.10 --no-tracing
```

## Features

Core utilities such as Tracing, Logging, Metrics, and Event Handler will be available across all Powertools languages. Additional utilities are subjective to each language ecosystem and customer demand.

| Utility                                                                                                                                                      | Description                                                                                                                                               |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [**Tracing**](./core/tracer.md)                                                                                                                              | Decorators and utilities to trace Lambda function handlers, and both synchronous and asynchronous functions                                               |
| [**Logger**](./core/logger.md)                                                                                                                               | Structured logging made easier, and decorator to enrich structured logging with key Lambda context details                                                |
| [**Metrics**](./core/metrics.md)                                                                                                                             | Custom Metrics created asynchronously via CloudWatch Embedded Metric Format (EMF)                                                                         |
| [**Event handler: AppSync**](./core/event_handler/appsync.md)                                                                                                | AppSync event handler for Lambda Direct Resolver and Amplify GraphQL Transformer function                                                                 |
| [**Event handler: API Gateway, ALB and Lambda Function URL**](https://awslabs.github.io/aws-lambda-powertools-python/latest/core/event_handler/api_gateway/) | Amazon API Gateway REST/HTTP API and ALB event handler for Lambda functions invoked using Proxy integration, and Lambda Function URL                      |
| [**Middleware factory**](./utilities/middleware_factory.md)                                                                                                  | Decorator factory to create your own middleware to run logic before, and after each Lambda invocation                                                     |
| [**Parameters**](./utilities/parameters.md)                                                                                                                  | Retrieve parameter values from AWS Systems Manager Parameter Store, AWS Secrets Manager, or Amazon DynamoDB, and cache them for a specific amount of time |
| [**Batch processing**](./utilities/batch.md)                                                                                                                 | Handle partial failures for AWS SQS batch processing                                                                                                      |
| [**Typing**](./utilities/typing.md)                                                                                                                          | Static typing classes to speedup development in your IDE                                                                                                  |
| [**Validation**](./utilities/validation.md)                                                                                                                  | JSON Schema validator for inbound events and responses                                                                                                    |
| [**Event source data classes**](./utilities/data_classes.md)                                                                                                 | Data classes describing the schema of common Lambda event triggers                                                                                        |
| [**Parser**](./utilities/parser.md)                                                                                                                          | Data parsing and deep validation using Pydantic                                                                                                           |
| [**Idempotency**](./utilities/idempotency.md)                                                                                                                | Idempotent Lambda handler                                                                                                                                 |
| [**Feature Flags**](./utilities/feature_flags.md)                                                                                                            | A simple rule engine to evaluate when one or multiple features should be enabled depending on the input                                                   |
| [**Streaming**](./utilities/streaming.md)                                                                                                                    | Streams datasets larger than the available memory as streaming data.                                                                                      |

## Environment variables

???+ info
	Explicit parameters take precedence over environment variables

| Environment variable                      | Description                                                                            | Utility                                                                             | Default               |
| ----------------------------------------- | -------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------- | --------------------- |
| **POWERTOOLS_SERVICE_NAME**               | Sets service name used for tracing namespace, metrics dimension and structured logging | All                                                                                 | `"service_undefined"` |
| **POWERTOOLS_METRICS_NAMESPACE**          | Sets namespace used for metrics                                                        | [Metrics](./core/metrics)                                                           | `None`                |
| **POWERTOOLS_TRACE_DISABLED**             | Explicitly disables tracing                                                            | [Tracing](./core/tracer)                                                            | `false`               |
| **POWERTOOLS_TRACER_CAPTURE_RESPONSE**    | Captures Lambda or method return as metadata.                                          | [Tracing](./core/tracer)                                                            | `true`                |
| **POWERTOOLS_TRACER_CAPTURE_ERROR**       | Captures Lambda or method exception as metadata.                                       | [Tracing](./core/tracer)                                                            | `true`                |
| **POWERTOOLS_TRACE_MIDDLEWARES**          | Creates sub-segment for each custom middleware                                         | [Middleware factory](./utilities/middleware_factory)                                | `false`               |
| **POWERTOOLS_LOGGER_LOG_EVENT**           | Logs incoming event                                                                    | [Logging](./core/logger)                                                            | `false`               |
| **POWERTOOLS_LOGGER_SAMPLE_RATE**         | Debug log sampling                                                                     | [Logging](./core/logger)                                                            | `0`                   |
| **POWERTOOLS_LOG_DEDUPLICATION_DISABLED** | Disables log deduplication filter protection to use Pytest Live Log feature            | [Logging](./core/logger)                                                            | `false`               |
| **POWERTOOLS_PARAMETERS_MAX_AGE**         | Adjust how long values are kept in cache (in seconds)                                  | [Parameters](./utilities/parameters/#adjusting-cache-ttl)                           | `5`                   |
| **POWERTOOLS_PARAMETERS_SSM_DECRYPT**     | Sets whether to decrypt or not values retrieved from AWS SSM Parameters Store          | [Parameters](./utilities/parameters/#ssmprovider)                                   | `false`               |
| **POWERTOOLS_DEV**                        | Increases verbosity across utilities                                                   | Multiple; see [POWERTOOLS_DEV effect below](#increasing-verbosity-across-utilities) | `false`               |
| **LOG_LEVEL**                             | Sets logging level                                                                     | [Logging](./core/logger)                                                            | `INFO`                |

### Optimizing for non-production environments

Whether you're prototyping locally or against a non-production environment, you can use `POWERTOOLS_DEV` to increase verbosity across multiple utilities.

???+ info
    We will emit a warning when `POWERTOOLS_DEV` is enabled to help you detect misuse in production environments.

When `POWERTOOLS_DEV` is set to a truthy value (`1`, `true`), it'll have the following effects:

| Utility           | Effect                                                                                                                                                       |
| ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Logger**        | Increase JSON indentation to 4. This will ease local debugging when running functions locally under emulators or direct calls while not affecting unit tests |
| **Event Handler** | Enable full traceback errors in the response, indent request/responses, and CORS in dev mode (`*`).                                                          |
| **Tracer**        | Future-proof safety to disables tracing operations in non-Lambda environments. This already happens automatically in the Tracer utility.                     |

## Debug mode

As a best practice for libraries, Powertools module logging statements are suppressed.

When necessary, you can use `POWERTOOLS_DEBUG` environment variable to enable debugging. This will provide additional information on every internal operation.

## How to support AWS Lambda Powertools for Python?

### Becoming a reference customer

Knowing which companies are using this library is important to help prioritize the project internally. If your company is using AWS Lambda Powertools for Python, you can request to have your name and logo added to the README file by raising a [Support Lambda Powertools (become a reference)](https://github.com/awslabs/aws-lambda-powertools-python/issues/new?assignees=&labels=customer-reference&template=support_powertools.yml&title=%5BSupport+Lambda+Powertools%5D%3A+%3Cyour+organization+name%3E){target="_blank"} issue.

The following companies, among others, use Powertools:

* [CPQi (Exadel Financial Services)](https://cpqi.com/){target="_blank"}
* [CloudZero](https://www.cloudzero.com/){target="_blank"}
* [CyberArk](https://www.cyberark.com/){target="_blank"}
* [globaldatanet](https://globaldatanet.com/){target="_blank"}
* [IMS](https://ims.tech/){target="_blank"}
* [Propellor.ai](https://www.propellor.ai/){target="_blank"}
* [TopSport](https://www.topsport.com.au/){target="_blank"}
* [Trek10](https://www.trek10.com/){target="_blank"}

### Sharing your work

Share what you did with Powertools 💞💞. Blog post, workshops, presentation, sample apps and others. Check out what the community has already shared about Powertools [here](https://awslabs.github.io/aws-lambda-powertools-python/latest/we_made_this/).

### Using Lambda Layer or SAR

This helps us understand who uses Powertools in a non-intrusive way, and helps us gain future investments for other Powertools languages. When [using Layers](https://awslabs.github.io/aws-lambda-powertools-python/latest/#lambda-layer), you can add Powertools as a dev dependency (or as part of your virtual env) to not impact the development process.

## Tenets

These are our core principles to guide our decision making.

* **AWS Lambda only**. We optimise for AWS Lambda function environments and supported runtimes only. Utilities might work with web frameworks and non-Lambda environments, though they are not officially supported.
* **Eases the adoption of best practices**. The main priority of the utilities is to facilitate best practices adoption, as defined in the AWS Well-Architected Serverless Lens; all other functionality is optional.
* **Keep it lean**. Additional dependencies are carefully considered for security and ease of maintenance, and prevent negatively impacting startup time.
* **We strive for backwards compatibility**. New features and changes should keep backwards compatibility. If a breaking change cannot be avoided, the deprecation and migration process should be clearly defined.
* **We work backwards from the community**. We aim to strike a balance of what would work best for 80% of customers. Emerging practices are considered and discussed via Requests for Comment (RFCs)
* **Progressive**. Utilities are designed to be incrementally adoptable for customers at any stage of their Serverless journey. They follow language idioms and their community’s common practices.
