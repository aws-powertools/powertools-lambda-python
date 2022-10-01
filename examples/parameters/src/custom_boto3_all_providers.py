import boto3
from botocore.config import Config

from aws_lambda_powertools.utilities import parameters

config = Config(region_name="us-west-1")

# construct boto clients with any custom configuration
ssm = boto3.client("ssm", config=config)
secrets = boto3.client("secrets", config=config)
appconfig = boto3.client("appconfigdata", config=config)
dynamodb = boto3.resource("dynamodb", config=config)

ssm_provider = parameters.SSMProvider(boto3_client=ssm)
secrets_provider = parameters.SecretsProvider(boto3_client=secrets)
appconf_provider = parameters.AppConfigProvider(boto3_client=appconfig, environment="my_env", application="my_app")
dynamodb_provider = parameters.DynamoDBProvider(boto3_client=dynamodb, table_name="my-table")
