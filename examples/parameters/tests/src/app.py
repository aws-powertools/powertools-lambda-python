from botocore.config import Config

from aws_lambda_powertools.utilities import parameters

ssm_provider = parameters.SSMProvider(config=Config(region_name="us-west-1"))


def handler(event, context):
    value = ssm_provider.get("/my/parameter")
    return {"message": value}
