---
title: Homepage
description: Powertools for AWS Lambda (Python)
---

<!-- markdownlint-disable MD043 MD013 -->

Powertools for AWS Lambda (Python) is a developer toolkit to implement Serverless best practices and increase developer velocity.

<!-- markdownlint-disable MD050 -->
<div class="grid cards" markdown>

- :material-battery-charging:{ .lg .middle } __Features__

    ---

    Adopt one, a few, or all industry practices. **Progressively**.

    [:octicons-arrow-right-24: All features](#features)

- :heart:{ .lg .middle } __Support this project__

    ---

    Become a public reference customer, share your work, contribute, use Lambda Layers, etc.

    [:octicons-arrow-right-24: Support](#support-powertools-for-aws-lambda-python)

- :material-file-code:{ .lg .middle } __Available languages__

    ---

    Powertools for AWS Lambda is also available in other languages

    :octicons-arrow-right-24: [Java](https://docs.powertools.aws.dev/lambda/java/){target="_blank"}, [TypeScript](https://docs.powertools.aws.dev/lambda/typescript/latest/){target="_blank" }, and [.NET](https://docs.powertools.aws.dev/lambda/dotnet/){target="_blank"}

</div>

## Install

You can install Powertools for AWS Lambda (Python) using your favorite dependency management, or Lambda Layers:

=== "Pip"

    Most features use Python standard library and the AWS SDK _(boto3)_ that are available in the AWS Lambda runtime.

    * **pip**: **`pip install "aws-lambda-powertools"`**{: .copyMe}:clipboard:
    * **poetry**: **`poetry add "aws-lambda-powertools"`**{: .copyMe}:clipboard:
    * **pdm**: **`pdm add "aws-lambda-powertools"`**{: .copyMe}:clipboard:

    ### Extra dependencies

    However, you will need additional dependencies if you are using any of the features below:

    | Feature                                                 | Install                                                                                  | Default dependency                                                           |
    | ------------------------------------------------------- | ---------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
    | **[Tracer](./core/tracer.md#install)**                  | **`pip install "aws-lambda-powertools[tracer]"`**{.copyMe}:clipboard:                    | `aws-xray-sdk`                                                               |
    | **[Validation](./utilities/validation.md#install)**     | **`pip install "aws-lambda-powertools[validation]"`**{.copyMe}:clipboard:                | `fastjsonschema`                                                             |
    | **[Parser](./utilities/parser.md#install)**             | **`pip install "aws-lambda-powertools[parser]"`**{.copyMe}:clipboard:                    | `pydantic` _(v1)_; [v2 is possible](./utilities/parser.md#using-pydantic-v2) |
    | **[Data Masking](./utilities/data_masking.md#install)** | **`pip install "aws-lambda-powertools[datamasking]"`**{.copyMe}:clipboard:               | `aws-encryption-sdk`, `jsonpath-ng`                                          |
    | **All extra dependencies at once**                      | **`pip install "aws-lambda-powertools[all]"`**{.copyMe}:clipboard:                       |
    | **Two or more extra dependencies only, not all**        | **`pip install "aws-lambda-powertools[tracer,parser,datamasking"]`**{.copyMe}:clipboard: |

=== "Lambda Layer"

    You can add our layer both in the [AWS Lambda Console _(under `Layers`)_](https://eu-west-1.console.aws.amazon.com/lambda/home#/add/layer){target="_blank"}, or via your favorite infrastructure as code framework with the ARN value.

    For the latter, make sure to replace `{region}` with your AWS region, e.g., `eu-west-1`.

    * <u>x86 architecture</u>: __arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV2:66__{: .copyMe}:clipboard:
    * <u>ARM architecture</u>: __arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66__{: .copyMe}:clipboard:

    ???+ note "Code snippets for popular infrastructure as code frameworks"

        === "x86_64"

            === "SAM"

                ```yaml hl_lines="5"
                MyLambdaFunction:
                    Type: AWS::Serverless::Function
                    Properties:
                        Layers:
                            - !Sub arn:aws:lambda:${AWS::Region}:017000801446:layer:AWSLambdaPowertoolsPythonV2:66
                ```

            === "Serverless framework"

                ```yaml hl_lines="5"
            	functions:
            		hello:
            		  handler: lambda_function.lambda_handler
            		  layers:
            			- arn:aws:lambda:${aws:region}:017000801446:layer:AWSLambdaPowertoolsPythonV2:66
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
                            layer_version_arn=f"arn:aws:lambda:{env.region}:017000801446:layer:AWSLambdaPowertoolsPythonV2:66"
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
                  layers 		= ["arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV2:66"]

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
                ? Enter up to 5 existing Lambda layer ARNs (comma-separated): arn:aws:lambda:eu-central-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:66
                ❯ amplify push -y


                # Updating an existing function and add the layer
                ❯ amplify update function
                ? Select the Lambda function you want to update test2
                General information
                - Name: <NAME-OF-FUNCTION>
                ? Which setting do you want to update? Lambda layers configuration
                ? Do you want to enable Lambda layers for this function? Yes
                ? Enter up to 5 existing Lambda layer ARNs (comma-separated): arn:aws:lambda:eu-central-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:66
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
                            - !Sub arn:aws:lambda:${AWS::Region}:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66
                ```

            === "Serverless framework"

                ```yaml hl_lines="6"
            	functions:
            		hello:
            		    handler: lambda_function.lambda_handler
                        architecture: arm64
            		    layers:
            		  	- arn:aws:lambda:${aws:region}:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66
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
                            layer_version_arn=f"arn:aws:lambda:{env.region}:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66"
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
                  layers 		= ["arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66"]
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
                ? Enter up to 5 existing Lambda layer ARNs (comma-separated): arn:aws:lambda:eu-central-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66
                ❯ amplify push -y


                # Updating an existing function and add the layer
                ❯ amplify update function
                ? Select the Lambda function you want to update test2
                General information
                - Name: <NAME-OF-FUNCTION>
                ? Which setting do you want to update? Lambda layers configuration
                ? Do you want to enable Lambda layers for this function? Yes
                ? Enter up to 5 existing Lambda layer ARNs (comma-separated): arn:aws:lambda:eu-central-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66
                ? Do you want to edit the local lambda function now? No
                ```

### Local development

!!! info "Using Lambda Layer? Simply add [**`"aws-lambda-powertools[all]"`**](#){: .copyMe}:clipboard: as a development dependency."

Powertools for AWS Lambda (Python) relies on the [AWS SDK bundled in the Lambda runtime](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html){target="_blank"}. This helps us achieve an optimal package size and initialization. However, when developing locally, you need to install AWS SDK as a development dependency to support IDE auto-completion and to run your tests locally:

- __Pip__: [**`pip install "aws-lambda-powertools[aws-sdk]"`**](#){: .copyMe}:clipboard:
- __Poetry__: [**`poetry add "aws-lambda-powertools[aws-sdk]" --group dev`**](#){: .copyMe}:clipboard:
- __Pdm__: [**`pdm add -dG "aws-lambda-powertools[aws-sdk]"`**](#){: .copyMe}:clipboard:

__A word about dependency resolution__

In this context, `[aws-sdk]` is an alias to the `boto3` package. Due to dependency resolution, it'll either install:

- __(A)__ the SDK version available in [Lambda runtime](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html){target="_blank"}
- __(B)__ a more up-to-date version if another package you use also depends on `boto3`, for example [Powertools for AWS Lambda (Python) Tracer](core/tracer.md){target="_blank"}

### Lambda Layer

[Lambda Layer](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html){target="_blank"} is a .zip file archive that can contain additional code, pre-packaged dependencies, data,  or configuration files. We compile and optimize [all dependencies](#install), and remove duplicate dependencies [already available in the Lambda runtime](https://github.com/aws-powertools/powertools-lambda-layer-cdk/blob/d24716744f7d1f37617b4998c992c4c067e19e64/layer/Python/Dockerfile#L36){target="_blank"} to achieve the most optimal size.

??? note "Click to expand and copy any regional Lambda Layer ARN"

    === "x86_64"

        | Region               | Layer ARN                                                                                                 |
        | -------------------- | --------------------------------------------------------------------------------------------------------- |
        | **`af-south-1`**     | **arn:aws:lambda:af-south-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:66**{: .copyMe}:clipboard:     |
        | **`ap-east-1`**      | **arn:aws:lambda:ap-east-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:66**{: .copyMe}:clipboard:      |
        | **`ap-northeast-1`** | **arn:aws:lambda:ap-northeast-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:66**{: .copyMe}:clipboard: |
        | **`ap-northeast-2`** | **arn:aws:lambda:ap-northeast-2:017000801446:layer:AWSLambdaPowertoolsPythonV2:66**{: .copyMe}:clipboard: |
        | **`ap-northeast-3`** | **arn:aws:lambda:ap-northeast-3:017000801446:layer:AWSLambdaPowertoolsPythonV2:66**{: .copyMe}:clipboard: |
        | **`ap-south-1`**     | **arn:aws:lambda:ap-south-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:66**{: .copyMe}:clipboard:     |
        | **`ap-south-2`**     | **arn:aws:lambda:ap-south-2:017000801446:layer:AWSLambdaPowertoolsPythonV2:66**{: .copyMe}:clipboard:     |
        | **`ap-southeast-1`** | **arn:aws:lambda:ap-southeast-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:66**{: .copyMe}:clipboard: |
        | **`ap-southeast-2`** | **arn:aws:lambda:ap-southeast-2:017000801446:layer:AWSLambdaPowertoolsPythonV2:66**{: .copyMe}:clipboard: |
        | **`ap-southeast-3`** | **arn:aws:lambda:ap-southeast-3:017000801446:layer:AWSLambdaPowertoolsPythonV2:66**{: .copyMe}:clipboard: |
        | **`ap-southeast-4`** | **arn:aws:lambda:ap-southeast-4:017000801446:layer:AWSLambdaPowertoolsPythonV2:66**{: .copyMe}:clipboard: |
        | **`ca-central-1`**   | **arn:aws:lambda:ca-central-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:66**{: .copyMe}:clipboard:   |
        | **`ca-west-1`**      | **arn:aws:lambda:ca-west-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:66**{: .copyMe}:clipboard:      |
        | **`eu-central-1`**   | **arn:aws:lambda:eu-central-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:66**{: .copyMe}:clipboard:   |
        | **`eu-central-2`**   | **arn:aws:lambda:eu-central-2:017000801446:layer:AWSLambdaPowertoolsPythonV2:66**{: .copyMe}:clipboard:   |
        | **`eu-north-1`**     | **arn:aws:lambda:eu-north-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:66**{: .copyMe}:clipboard:     |
        | **`eu-south-1`**     | **arn:aws:lambda:eu-south-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:66**{: .copyMe}:clipboard:     |
        | **`eu-south-2`**     | **arn:aws:lambda:eu-south-2:017000801446:layer:AWSLambdaPowertoolsPythonV2:66**{: .copyMe}:clipboard:     |
        | **`eu-west-1`**      | **arn:aws:lambda:eu-west-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:66**{: .copyMe}:clipboard:      |
        | **`eu-west-2`**      | **arn:aws:lambda:eu-west-2:017000801446:layer:AWSLambdaPowertoolsPythonV2:66**{: .copyMe}:clipboard:      |
        | **`eu-west-3`**      | **arn:aws:lambda:eu-west-3:017000801446:layer:AWSLambdaPowertoolsPythonV2:66**{: .copyMe}:clipboard:      |
        | **`il-central-1`**   | **arn:aws:lambda:il-central-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:66**{: .copyMe}:clipboard:   |
        | **`me-central-1`**   | **arn:aws:lambda:me-central-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:66**{: .copyMe}:clipboard:   |
        | **`me-south-1`**     | **arn:aws:lambda:me-south-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:66**{: .copyMe}:clipboard:     |
        | **`sa-east-1`**      | **arn:aws:lambda:sa-east-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:66**{: .copyMe}:clipboard:      |
        | **`us-east-1`**      | **arn:aws:lambda:us-east-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:66**{: .copyMe}:clipboard:      |
        | **`us-east-2`**      | **arn:aws:lambda:us-east-2:017000801446:layer:AWSLambdaPowertoolsPythonV2:66**{: .copyMe}:clipboard:      |
        | **`us-west-1`**      | **arn:aws:lambda:us-west-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:66**{: .copyMe}:clipboard:      |
        | **`us-west-2`**      | **arn:aws:lambda:us-west-2:017000801446:layer:AWSLambdaPowertoolsPythonV2:66**{: .copyMe}:clipboard:      |

    === "arm64"

        | Region               | Layer ARN                                                                                                       |
        | -------------------- | --------------------------------------------------------------------------------------------------------------- |
        | **`af-south-1`**     | **arn:aws:lambda:af-south-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66**{: .copyMe}:clipboard:     |
        | **`ap-east-1`**      | **arn:aws:lambda:ap-east-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66**{: .copyMe}:clipboard:      |
        | **`ap-northeast-1`** | **arn:aws:lambda:ap-northeast-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66**{: .copyMe}:clipboard: |
        | **`ap-northeast-2`** | **arn:aws:lambda:ap-northeast-2:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66**{: .copyMe}:clipboard: |
        | **`ap-northeast-3`** | **arn:aws:lambda:ap-northeast-3:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66**{: .copyMe}:clipboard: |
        | **`ap-south-1`**     | **arn:aws:lambda:ap-south-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66**{: .copyMe}:clipboard:     |
        | **`ap-south-2`**     | **arn:aws:lambda:ap-south-2:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66**{: .copyMe}:clipboard:     |
        | **`ap-southeast-1`** | **arn:aws:lambda:ap-southeast-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66**{: .copyMe}:clipboard: |
        | **`ap-southeast-2`** | **arn:aws:lambda:ap-southeast-2:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66**{: .copyMe}:clipboard: |
        | **`ap-southeast-3`** | **arn:aws:lambda:ap-southeast-3:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66**{: .copyMe}:clipboard: |
        | **`ca-central-1`**   | **arn:aws:lambda:ca-central-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66**{: .copyMe}:clipboard:   |
        | **`eu-central-1`**   | **arn:aws:lambda:eu-central-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66**{: .copyMe}:clipboard:   |
        | **`eu-central-2`**   | **arn:aws:lambda:eu-central-2:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66**{: .copyMe}:clipboard:   |
        | **`eu-north-1`**     | **arn:aws:lambda:eu-north-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66**{: .copyMe}:clipboard:     |
        | **`eu-south-1`**     | **arn:aws:lambda:eu-south-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66**{: .copyMe}:clipboard:     |
        | **`eu-south-2`**     | **arn:aws:lambda:eu-south-2:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66**{: .copyMe}:clipboard:     |
        | **`eu-west-1`**      | **arn:aws:lambda:eu-west-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66**{: .copyMe}:clipboard:      |
        | **`eu-west-2`**      | **arn:aws:lambda:eu-west-2:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66**{: .copyMe}:clipboard:      |
        | **`eu-west-3`**      | **arn:aws:lambda:eu-west-3:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66**{: .copyMe}:clipboard:      |
        | **`il-central-1`**   | **arn:aws:lambda:il-central-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66**{: .copyMe}:clipboard:   |
        | **`me-central-1`**   | **arn:aws:lambda:me-central-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66**{: .copyMe}:clipboard:   |
        | **`me-south-1`**     | **arn:aws:lambda:me-south-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66**{: .copyMe}:clipboard:     |
        | **`sa-east-1`**      | **arn:aws:lambda:sa-east-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66**{: .copyMe}:clipboard:      |
        | **`us-east-1`**      | **arn:aws:lambda:us-east-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66**{: .copyMe}:clipboard:      |
        | **`us-east-2`**      | **arn:aws:lambda:us-east-2:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66**{: .copyMe}:clipboard:      |
        | **`us-west-1`**      | **arn:aws:lambda:us-west-1:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66**{: .copyMe}:clipboard:      |
        | **`us-west-2`**      | **arn:aws:lambda:us-west-2:017000801446:layer:AWSLambdaPowertoolsPythonV2-Arm64:66**{: .copyMe}:clipboard:      |

**Want to inspect the contents of the Layer?**

The pre-signed URL to download this Lambda Layer will be within `Location` key in the CLI output. The CLI output will also contain the Powertools for AWS Lambda version it contains.

```bash title="AWS CLI command to download Lambda Layer content"
aws lambda get-layer-version-by-arn --arn arn:aws:lambda:eu-west-1:017000801446:layer:AWSLambdaPowertoolsPythonV2:66 --region eu-west-1
```

#### SAR

Serverless Application Repository (SAR) App deploys a CloudFormation stack with a copy of our Lambda Layer in your AWS account and region.

Compared with the [public Layer ARN](#lambda-layer) option, SAR allows you to choose a semantic version and deploys a Layer in your target account.

| App                                                                                                                                                                                 | ARN                                                                                                                            | Description                                                           |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------- |
| [**aws-lambda-powertools-python-layer**](https://serverlessrepo.aws.amazon.com/applications/eu-west-1/057560766410/aws-lambda-powertools-python-layer){target="_blank"}             | [arn:aws:serverlessrepo:eu-west-1:057560766410:applications/aws-lambda-powertools-python-layer](#){: .copyMe}:clipboard:       | Contains all extra dependencies (e.g: pydantic).                      |
| [**aws-lambda-powertools-python-layer-arm64**](https://serverlessrepo.aws.amazon.com/applications/eu-west-1/057560766410/aws-lambda-powertools-python-layer-arm64){target="_blank"} | [arn:aws:serverlessrepo:eu-west-1:057560766410:applications/aws-lambda-powertools-python-layer-arm64](#){: .copyMe}:clipboard: | Contains all extra dependencies (e.g: pydantic). For arm64 functions. |

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
                        # Find latest from github.com/aws-powertools/powertools-lambda-python/releases
                        SemanticVersion: 2.0.0
        ```

    === "CDK"

        ```python hl_lines="14 22-23 31"
        from aws_cdk import core, aws_sam as sam, aws_lambda

        POWERTOOLS_BASE_NAME = 'AWSLambdaPowertools'
        # Find latest from github.com/aws-powertools/powertools-lambda-python/releases
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

    	> Credits to [Dani Comnea](https://github.com/DanyC97){target="_blank" rel="nofollow"} for providing the Terraform equivalent.

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
          description = "The Powertools for AWS Lambda (Python) release version"
        }

        output "deployed_powertools_sar_version" {
          value = data.aws_serverlessapplicationrepository_application.sar_app.semantic_version
        }

    	# Fetch Powertools for AWS Lambda (Python) Layer ARN from deployed SAR App
    	output "aws_lambda_powertools_layer_arn" {
    	  value = aws_serverlessapplicationrepository_cloudformation_stack.deploy_sar_stack.outputs.LayerVersionArn
    	}
        ```

    Credits to [mwarkentin](https://github.com/mwarkentin){target="_blank" rel="nofollow"} for providing the scoped down IAM permissions below.

    ```yaml hl_lines="21-52" title="Least-privileged IAM permissions SAM example"
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
                    # this is arn of the Powertools for AWS Lambda (Python) SAR app
                    - arn:aws:serverlessrepo:eu-west-1:057560766410:applications/aws-lambda-powertools-python-layer
                - Sid: S3AccessLayer
                Effect: Allow
                Action:
                    - s3:GetObject
                Resource:
                    # AWS publishes to an external S3 bucket locked down to your account ID
                    # The below example is us publishing Powertools for AWS Lambda (Python)
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

## Quick getting started

```bash title="Hello world example using SAM CLI"
sam init --app-template hello-world-powertools-python --name sam-app --package-type Zip --runtime python3.11 --no-tracing
```

## Features

Core utilities such as Tracing, Logging, Metrics, and Event Handler will be available across all Powertools for AWS Lambda languages. Additional utilities are subjective to each language ecosystem and customer demand.

| Utility                                                                                                                                             | Description                                                                                                                                               |
| --------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [__Tracing__](./core/tracer.md){target="_blank"}                                                                                                    | Decorators and utilities to trace Lambda function handlers, and both synchronous and asynchronous functions                                               |
| [__Logger__](./core/logger.md){target="_blank"}                                                                                                     | Structured logging made easier, and decorator to enrich structured logging with key Lambda context details                                                |
| [__Metrics__](./core/metrics.md){target="_blank"}                                                                                                   | Custom Metrics created asynchronously via CloudWatch Embedded Metric Format (EMF)                                                                         |
| [__Event handler: AppSync__](./core/event_handler/appsync.md){target="_blank"}                                                                      | AppSync event handler for Lambda Direct Resolver and Amplify GraphQL Transformer function                                                                 |
| [__Event handler: API Gateway, ALB and Lambda Function URL__](https://docs.powertools.aws.dev/lambda/python/latest/core/event_handler/api_gateway/) | Amazon API Gateway REST/HTTP API and ALB event handler for Lambda functions invoked using Proxy integration, and Lambda Function URL                      |
| [__Middleware factory__](./utilities/middleware_factory.md){target="_blank"}                                                                        | Decorator factory to create your own middleware to run logic before, and after each Lambda invocation                                                     |
| [__Parameters__](./utilities/parameters.md){target="_blank"}                                                                                        | Retrieve parameter values from AWS Systems Manager Parameter Store, AWS Secrets Manager, or Amazon DynamoDB, and cache them for a specific amount of time |
| [__Batch processing__](./utilities/batch.md){target="_blank"}                                                                                       | Handle partial failures for AWS SQS batch processing                                                                                                      |
| [__Typing__](./utilities/typing.md){target="_blank"}                                                                                                | Static typing classes to speedup development in your IDE                                                                                                  |
| [__Validation__](./utilities/validation.md){target="_blank"}                                                                                        | JSON Schema validator for inbound events and responses                                                                                                    |
| [__Event source data classes__](./utilities/data_classes.md){target="_blank"}                                                                       | Data classes describing the schema of common Lambda event triggers                                                                                        |
| [__Parser__](./utilities/parser.md){target="_blank"}                                                                                                | Data parsing and deep validation using Pydantic                                                                                                           |
| [__Idempotency__](./utilities/idempotency.md){target="_blank"}                                                                                      | Idempotent Lambda handler                                                                                                                                 |
| [__Data Masking__](./utilities/data_masking.md){target="_blank"}                                                                                    | Protect confidential data with easy removal or encryption                                                                                                 |
| [__Feature Flags__](./utilities/feature_flags.md){target="_blank"}                                                                                  | A simple rule engine to evaluate when one or multiple features should be enabled depending on the input                                                   |
| [__Streaming__](./utilities/streaming.md){target="_blank"}                                                                                          | Streams datasets larger than the available memory as streaming data.                                                                                      |

## Environment variables

???+ info
	Explicit parameters take precedence over environment variables

| Environment variable                      | Description                                                                            | Utility                                                                                  | Default               |
| ----------------------------------------- | -------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- | --------------------- |
| __POWERTOOLS_SERVICE_NAME__               | Sets service name used for tracing namespace, metrics dimension and structured logging | All                                                                                      | `"service_undefined"` |
| __POWERTOOLS_METRICS_NAMESPACE__          | Sets namespace used for metrics                                                        | [Metrics](./core/metrics.md){target="_blank"}                                            | `None`                |
| __POWERTOOLS_TRACE_DISABLED__             | Explicitly disables tracing                                                            | [Tracing](./core/tracer.md){target="_blank"}                                             | `false`               |
| __POWERTOOLS_TRACER_CAPTURE_RESPONSE__    | Captures Lambda or method return as metadata.                                          | [Tracing](./core/tracer.md){target="_blank"}                                             | `true`                |
| __POWERTOOLS_TRACER_CAPTURE_ERROR__       | Captures Lambda or method exception as metadata.                                       | [Tracing](./core/tracer.md){target="_blank"}                                             | `true`                |
| __POWERTOOLS_TRACE_MIDDLEWARES__          | Creates sub-segment for each custom middleware                                         | [Middleware factory](./utilities/middleware_factory.md){target="_blank"}                 | `false`               |
| __POWERTOOLS_LOGGER_LOG_EVENT__           | Logs incoming event                                                                    | [Logging](./core/logger.md){target="_blank"}                                             | `false`               |
| __POWERTOOLS_LOGGER_SAMPLE_RATE__         | Debug log sampling                                                                     | [Logging](./core/logger.md){target="_blank"}                                             | `0`                   |
| __POWERTOOLS_LOG_DEDUPLICATION_DISABLED__ | Disables log deduplication filter protection to use Pytest Live Log feature            | [Logging](./core/logger.md){target="_blank"}                                             | `false`               |
| __POWERTOOLS_PARAMETERS_MAX_AGE__         | Adjust how long values are kept in cache (in seconds)                                  | [Parameters](./utilities/parameters.md#adjusting-cache-ttl){target="_blank"}             | `5`                   |
| __POWERTOOLS_PARAMETERS_SSM_DECRYPT__     | Sets whether to decrypt or not values retrieved from AWS SSM Parameters Store          | [Parameters](./utilities/parameters.md#ssmprovider){target="_blank"}                     | `false`               |
| __POWERTOOLS_DEV__                        | Increases verbosity across utilities                                                   | Multiple; see [POWERTOOLS_DEV effect below](#optimizing-for-non-production-environments) | `false`               |
| __POWERTOOLS_LOG_LEVEL__                  | Sets logging level                                                                     | [Logging](./core/logger.md){target="_blank"}                                             | `INFO`                |

### Optimizing for non-production environments

!!! info "We will emit a warning when this feature is used to help you detect misuse in production."

Whether you're prototyping locally or against a non-production environment, you can use `POWERTOOLS_DEV` to increase verbosity across multiple utilities.

When `POWERTOOLS_DEV` is set to a truthy value (`1`, `true`), it'll have the following effects:

| Utility           | Effect                                                                                                                                                                                                                                                                 |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| __Logger__        | Increase JSON indentation to 4. This will ease local debugging when running functions locally under emulators or direct calls while not affecting unit tests. <br><br> However, Amazon CloudWatch Logs view will degrade as each new line is treated as a new message. |
| __Event Handler__ | Enable full traceback errors in the response, indent request/responses, and CORS in dev mode (`*`).                                                                                                                                                                    |
| __Tracer__        | Future-proof safety to disables tracing operations in non-Lambda environments. This already happens automatically in the Tracer utility.                                                                                                                               |

## Debug mode

As a best practice for libraries, Powertools module logging statements are suppressed.

When necessary, you can use `POWERTOOLS_DEBUG` environment variable to enable debugging. This will provide additional information on every internal operation.

## Support Powertools for AWS Lambda (Python)

There are many ways you can help us gain future investments to improve everyone's experience:

<div class="grid cards" markdown>

- :heart:{ .lg .middle } __Become a public reference__

    ---

    Add your company name and logo on our [landing page](https://powertools.aws.dev).

    [:octicons-arrow-right-24: GitHub Issue template]((https://github.com/aws-powertools/powertools-lambda-python/issues/new?assignees=&labels=customer-reference&template=support_powertools.yml&title=%5BSupport+Lambda+Powertools%5D%3A+%3Cyour+organization+name%3E){target="_blank"})

- :mega:{ .lg .middle } __Share your work__

    ---

    Blog posts, video, and sample projects about Powertools for AWS Lambda.

    [:octicons-arrow-right-24: GitHub Issue template](https://github.com/aws-powertools/powertools-lambda-python/issues/new?assignees=&labels=community-content&template=share_your_work.yml&title=%5BI+Made+This%5D%3A+%3CTITLE%3E){target="_blank"}

- :partying_face:{ .lg .middle } __Join the community__

    ---

    Connect, ask questions, and share what features you use.

    [:octicons-arrow-right-24: Discord invite](https://discord.gg/B8zZKbbyET){target="blank"}

</div>

### Becoming a reference customer

Knowing which companies are using this library is important to help prioritize the project internally. The following companies, among others, use Powertools:

<div class="grid" style="text-align:center;" markdown>

[**Capital One**](https://www.capitalone.com/){target="_blank" rel="nofollow"}
{ .card }

[**CPQi (Exadel Financial Services)**](https://cpqi.com/){target="_blank" rel="nofollow"}
{ .card }

[**CloudZero**](https://www.cloudzero.com/){target="_blank" rel="nofollow"}
{ .card }

[**CyberArk**](https://www.cyberark.com/){target="_blank" rel="nofollow"}
{ .card }

[**globaldatanet**](https://globaldatanet.com/){target="_blank" rel="nofollow"}
{ .card }

[**IMS**](https://ims.tech/){target="_blank" rel="nofollow"}
{ .card }

[**Jit Security**](https://www.jit.io/){target="_blank" rel="nofollow"}
{ .card }

[**Propellor.ai**](https://www.propellor.ai/){target="_blank" rel="nofollow"}
{ .card }

[**TopSport**](https://www.topsport.com.au/){target="_blank" rel="nofollow"}
{ .card }

[**Transformity**](https://transformity.tech/){target="_blank" rel="nofollow"}
{ .card }

[**Trek10**](https://www.trek10.com/){target="_blank" rel="nofollow"}
{ .card }

[**Vertex Pharmaceuticals**](https://www.vrtx.com/){target="_blank" rel="nofollow"}
{ .card }

[**Alma Media**](https://www.almamedia.fi/en/){target="_blank" rel="nofollow}
{ .card }

</div>

### Using Lambda Layers

!!! note "Layers help us understand who uses Powertools for AWS Lambda (Python) in a non-intrusive way."

When [using Layers](#lambda-layer), you can add Powertools for AWS Lambda (Python) as a dev dependency to not impact the development process. For Layers, we pre-package all dependencies, compile and optimize for storage and both x86 and ARM architecture.

## Tenets

These are our core principles to guide our decision making.

- __AWS Lambda only__. We optimise for AWS Lambda function environments and supported runtimes only. Utilities might work with web frameworks and non-Lambda environments, though they are not officially supported.
- __Eases the adoption of best practices__. The main priority of the utilities is to facilitate best practices adoption, as defined in the AWS Well-Architected Serverless Lens; all other functionality is optional.
- __Keep it lean__. Additional dependencies are carefully considered for security and ease of maintenance, and prevent negatively impacting startup time.
- __We strive for backwards compatibility__. New features and changes should keep backwards compatibility. If a breaking change cannot be avoided, the deprecation and migration process should be clearly defined.
- __We work backwards from the community__. We aim to strike a balance of what would work best for 80% of customers. Emerging practices are considered and discussed via Requests for Comment (RFCs)
- __Progressive__. Utilities are designed to be incrementally adoptable for customers at any stage of their Serverless journey. They follow language idioms and their community’s common practices.
