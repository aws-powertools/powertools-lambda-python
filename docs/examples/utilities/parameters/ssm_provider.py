from botocore.config import Config

from aws_lambda_powertools.utilities import parameters

config = Config(region_name="us-west-1")
ssm_provider = parameters.SSMProvider(config=config)  # or boto3_session=boto3.Session()


def handler(event, context):
    # Retrieve a single parameter
    value = ssm_provider.get("/my/parameter")

    # Retrieve multiple parameters from a path prefix
    values = ssm_provider.get_multiple("/my/path/prefix")
    for k, v in values.items():
        print(f"{k}: {v}")
