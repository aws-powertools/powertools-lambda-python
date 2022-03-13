from botocore.config import Config

from aws_lambda_powertools.utilities import parameters

config = Config(region_name="us-west-1")
appconf_provider = parameters.AppConfigProvider(
    environment="my_env",
    application="my_app",
    config=config,
)


def handler(event, context):
    # Retrieve a single secret
    value: bytes = appconf_provider.get("my_conf")
