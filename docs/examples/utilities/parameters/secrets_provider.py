from botocore.config import Config

from aws_lambda_powertools.utilities import parameters

config = Config(region_name="us-west-1")
secrets_provider = parameters.SecretsProvider(config=config)


def handler(event, context):
    # Retrieve a single secret
    value = secrets_provider.get("my-secret")
