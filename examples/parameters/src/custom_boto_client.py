import boto3

from aws_lambda_powertools.utilities import parameters

boto3_client = boto3.client("ssm")
ssm_provider = parameters.SSMProvider(boto3_client=boto3_client)


def handler(event, context):
    # Retrieve a single parameter
    value = ssm_provider.get("/my/parameter")

    return value
