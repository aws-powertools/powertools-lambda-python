from botocore.config import Config

from aws_lambda_powertools.utilities import parameters

boto_config = Config()
ssm_provider = parameters.SSMProvider(config=boto_config)


def handler(event, context):
    # Retrieve a single parameter
    value = ssm_provider.get("/my/parameter")

    return value
