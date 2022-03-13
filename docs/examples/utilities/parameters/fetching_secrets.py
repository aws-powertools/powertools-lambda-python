from aws_lambda_powertools.utilities import parameters


def handler(event, context):
    # Retrieve a single secret
    value = parameters.get_secret("my-secret")
