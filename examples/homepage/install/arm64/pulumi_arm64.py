import json

import pulumi
import pulumi_aws as aws

role = aws.iam.Role(
    "role",
    assume_role_policy=json.dumps(
        {
            "Version": "2012-10-17",
            "Statement": [
                {"Action": "sts:AssumeRole", "Principal": {"Service": "lambda.amazonaws.com"}, "Effect": "Allow"},
            ],
        },
    ),
    managed_policy_arns=[aws.iam.ManagedPolicy.AWS_LAMBDA_BASIC_EXECUTION_ROLE],
)

lambda_function = aws.lambda_.Function(
    "function",
    layers=[
        pulumi.Output.concat(
            "arn:aws:lambda:",
            aws.get_region_output().name,
            ":017000801446:layer:AWSLambdaPowertoolsPythonV3-python312-arm64:6",
        ),
    ],
    tracing_config={"mode": "Active"},
    runtime=aws.lambda_.Runtime.PYTHON3D12,
    handler="index.handler",
    role=role.arn,
    architectures=["arm64"],
    code=pulumi.FileArchive("lambda_function_payload.zip"),
)
