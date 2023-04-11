import boto3

from aws_lambda_powertools.utilities import parameters

boto3_session = boto3.session.Session()
ssm_provider = parameters.SSMProvider(boto3_session=boto3_session)


def handler(event, context):
    # Retrieve a single parameter
    value = ssm_provider.get("/my/parameter")

    return value
