---
title: Installation
description: Installing Powertools for AWS Lambda (Python)
---

<!-- markdownlint-disable MD043 MD013 -->

## Package manager

Most features use Python standard library and the AWS SDK _(boto3)_ that are available in the AWS Lambda runtime.

=== "pip"

    ```bash
    pip install "aws-lambda-powertools"
    ```

=== "poetry"

    ```bash
    poetry add "aws-lambda-powertools"
    ```

=== "pdm"

    ```bash
    pdm add "aws-lambda-powertools"
    ```

=== "uv"

    ```bash
    uv add "aws-lambda-powertools"
    ```

### Extra dependencies

Some features require additional dependencies. Install them as needed:

| Feature | Install | Default dependency |
| ------- | ------- | ------------------ |
| [Tracer](../core/tracer.md) | `pip install "aws-lambda-powertools[tracer]"` | `aws-xray-sdk` |
| [Validation](../utilities/validation.md) | `pip install "aws-lambda-powertools[validation]"` | `fastjsonschema` |
| [Parser](../utilities/parser.md) | `pip install "aws-lambda-powertools[parser]"` | `pydantic` |
| [Data Masking](../utilities/data_masking.md) | `pip install "aws-lambda-powertools[datamasking]"` | `aws-encryption-sdk`, `jsonpath-ng` |
| [Datadog Metrics](../core/metrics/datadog.md) | `pip install "aws-lambda-powertools[datadog]"` | `datadog-lambda` |
| [Kafka (Avro)](../utilities/kafka.md) | `pip install "aws-lambda-powertools[kafka-consumer-avro]"` | `avro` |
| [Kafka (Protobuf)](../utilities/kafka.md) | `pip install "aws-lambda-powertools[kafka-consumer-protobuf]"` | `protobuf` |
| Redis | `pip install "aws-lambda-powertools[redis]"` | `redis` |
| Valkey | `pip install "aws-lambda-powertools[valkey]"` | `valkey-glide` |
| All at once | `pip install "aws-lambda-powertools[all]"` | All core extras |

### Local development

Powertools for AWS Lambda (Python) relies on the AWS SDK bundled in the Lambda runtime. When developing locally, install the SDK as a dev dependency:

```bash
pip install "aws-lambda-powertools[aws-sdk]"
```

### Alpha releases

We publish `prerelease` versions to PyPi for early feedback on unstable releases.

=== "pip"

    ```bash
    pip install --pre "aws-lambda-powertools"
    ```

=== "poetry"

    ```bash
    poetry add --allow-prereleases "aws-lambda-powertools" --group dev
    ```

=== "uv"

    ```bash
    uv add --prerelease allow "aws-lambda-powertools"
    ```

## Lambda Layer

[Lambda Layer](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html){target="_blank"} is a .zip file archive that contains pre-packaged dependencies. We compile and optimize all dependencies for both x86_64 and ARM architectures.

Replace `{region}` with your AWS region (e.g., `eu-west-1`) and `{python_version}` without the period (e.g., `python313` for Python 3.13).

| Architecture | Layer ARN |
| ------------ | --------- |
| x86_64 | `arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-{python_version}-x86_64:27` |
| ARM64 | `arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-{python_version}-arm64:27` |

### All regional Layer ARNs

=== "x86_64"
    --8<-- "docs/includes/_layer_homepage_x86.md"

=== "arm64"
    --8<-- "docs/includes/_layer_homepage_arm64.md"

??? tip "Want to inspect the Layer contents?"
    ```bash
    aws lambda get-layer-version-by-arn --arn arn:aws:lambda:eu-west-1:017000801446:layer:AWSLambdaPowertoolsPythonV3-python313-x86_64:27 --region eu-west-1
    ```
    The pre-signed URL will be in the `Location` key.

### Using SSM Parameter Store

We publish Layer ARNs to SSM Parameter Store for easier automation:

=== "CloudFormation"

    ```yaml
    MyFunction:
      Type: AWS::Lambda::Function
      Properties:
        Layers:
          - !Sub "{{resolve:ssm:/aws/service/powertools/python/${Architecture}/${PythonVersion}/latest}}"
    ```

=== "Terraform"

    ```hcl
    data "aws_ssm_parameter" "powertools" {
      name = "/aws/service/powertools/python/x86_64/python3.13/latest"
    }

    resource "aws_lambda_function" "example" {
      layers = [data.aws_ssm_parameter.powertools.value]
    }
    ```

### Infrastructure as Code examples

=== "SAM"

    ```yaml hl_lines="11"
    --8<-- "examples/homepage/install/x86_64/sam.yaml"
    ```

=== "CDK"

    ```python hl_lines="13 19"
    --8<-- "examples/homepage/install/x86_64/cdk_x86.py"
    ```

=== "Serverless Framework"

    ```yaml hl_lines="13"
    --8<-- "examples/homepage/install/x86_64/serverless.yml"
    ```

=== "Terraform"

    ```terraform hl_lines="9 37"
    --8<-- "examples/homepage/install/x86_64/terraform.tf"
    ```

=== "Pulumi"

    ```python hl_lines="21-27"
    --8<-- "examples/homepage/install/x86_64/pulumi_x86.py"
    ```

### AWS China regions

| Region | Architecture | Layer ARN |
| ------ | ------------ | --------- |
| cn-north-1 | x86_64 | `arn:aws-cn:lambda:cn-north-1:498634801083:layer:AWSLambdaPowertoolsPythonV3-{python_version}-x86_64:27` |
| cn-north-1 | ARM64 | `arn:aws-cn:lambda:cn-north-1:498634801083:layer:AWSLambdaPowertoolsPythonV3-{python_version}-arm64:27` |

### AWS GovCloud regions

| Region | Architecture | Layer ARN |
| ------ | ------------ | --------- |
| us-gov-east-1 | x86_64 | `arn:aws-us-gov:lambda:us-gov-east-1:165087284144:layer:AWSLambdaPowertoolsPythonV3-{python_version}-x86_64:27` |
| us-gov-east-1 | ARM64 | `arn:aws-us-gov:lambda:us-gov-east-1:165087284144:layer:AWSLambdaPowertoolsPythonV3-{python_version}-arm64:27` |
| us-gov-west-1 | x86_64 | `arn:aws-us-gov:lambda:us-gov-west-1:165093116878:layer:AWSLambdaPowertoolsPythonV3-{python_version}-x86_64:27` |
| us-gov-west-1 | ARM64 | `arn:aws-us-gov:lambda:us-gov-west-1:165093116878:layer:AWSLambdaPowertoolsPythonV3-{python_version}-arm64:27` |

## Serverless Application Repository (SAR)

SAR deploys a CloudFormation stack with a copy of our Lambda Layer in your account. This allows you to use semantic versioning.

| Python | Architecture | SAR App |
| ------ | ------------ | ------- |
| 3.10 | x86_64 | [aws-lambda-powertools-python-layer-v3-python310-x86-64](https://serverlessrepo.aws.amazon.com/applications/eu-west-1/057560766410/aws-lambda-powertools-python-layer-v3-python310-x86-64){target="_blank"} |
| 3.11 | x86_64 | [aws-lambda-powertools-python-layer-v3-python311-x86-64](https://serverlessrepo.aws.amazon.com/applications/eu-west-1/057560766410/aws-lambda-powertools-python-layer-v3-python311-x86-64){target="_blank"} |
| 3.12 | x86_64 | [aws-lambda-powertools-python-layer-v3-python312-x86-64](https://serverlessrepo.aws.amazon.com/applications/eu-west-1/057560766410/aws-lambda-powertools-python-layer-v3-python312-x86-64){target="_blank"} |
| 3.13 | x86_64 | [aws-lambda-powertools-python-layer-v3-python313-x86-64](https://serverlessrepo.aws.amazon.com/applications/eu-west-1/057560766410/aws-lambda-powertools-python-layer-v3-python313-x86-64){target="_blank"} |
| 3.14 | x86_64 | [aws-lambda-powertools-python-layer-v3-python314-x86-64](https://serverlessrepo.aws.amazon.com/applications/eu-west-1/057560766410/aws-lambda-powertools-python-layer-v3-python314-x86-64){target="_blank"} |
| 3.10 | ARM64 | [aws-lambda-powertools-python-layer-v3-python310-arm64](https://serverlessrepo.aws.amazon.com/applications/eu-west-1/057560766410/aws-lambda-powertools-python-layer-v3-python310-arm64){target="_blank"} |
| 3.11 | ARM64 | [aws-lambda-powertools-python-layer-v3-python311-arm64](https://serverlessrepo.aws.amazon.com/applications/eu-west-1/057560766410/aws-lambda-powertools-python-layer-v3-python311-arm64){target="_blank"} |
| 3.12 | ARM64 | [aws-lambda-powertools-python-layer-v3-python312-arm64](https://serverlessrepo.aws.amazon.com/applications/eu-west-1/057560766410/aws-lambda-powertools-python-layer-v3-python312-arm64){target="_blank"} |
| 3.13 | ARM64 | [aws-lambda-powertools-python-layer-v3-python313-arm64](https://serverlessrepo.aws.amazon.com/applications/eu-west-1/057560766410/aws-lambda-powertools-python-layer-v3-python313-arm64){target="_blank"} |
| 3.14 | ARM64 | [aws-lambda-powertools-python-layer-v3-python314-arm64](https://serverlessrepo.aws.amazon.com/applications/eu-west-1/057560766410/aws-lambda-powertools-python-layer-v3-python314-arm64){target="_blank"} |

??? note "SAR Infrastructure as Code examples"

    === "SAM"

        ```yaml hl_lines="6 9 10 17-19"
        --8<-- "examples/homepage/install/sar/sam.yaml"
        ```

    === "CDK"

        ```python hl_lines="7 16-20 23-27"
        --8<-- "examples/homepage/install/sar/cdk_sar.py"
        ```

    === "Terraform"

        ```terraform hl_lines="12-13 15-20 23-25 40"
        --8<-- "examples/homepage/install/sar/terraform.tf"
        ```

    ??? question "Need least-privilege IAM permissions?"

        ```yaml hl_lines="21-52"
        --8<-- "examples/homepage/install/sar/scoped_down_iam.yaml"
        ```
