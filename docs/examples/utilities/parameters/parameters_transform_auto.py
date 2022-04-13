from aws_lambda_powertools.utilities import parameters

ssm_provider = parameters.SSMProvider()


def handler(event, context):
    values = ssm_provider.get_multiple("/param", transform="auto")
