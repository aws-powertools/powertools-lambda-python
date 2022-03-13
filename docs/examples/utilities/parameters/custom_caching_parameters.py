from botocore.config import Config

from aws_lambda_powertools.utilities import parameters

config = Config(region_name="us-west-1")
ssm_provider = parameters.SSMProvider(config=config)


def handler(event, context):
    # Retrieve a single parameter
    value = ssm_provider.get("/my/parameter", max_age=60)  # 1 minute

    # Retrieve multiple parameters from a path prefix
    values = ssm_provider.get_multiple("/my/path/prefix", max_age=60)
    for k, v in values.items():
        print(f"{k}: {v}")
