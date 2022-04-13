from aws_lambda_powertools.utilities import parameters


def handler(event, context):
    # Retrieve a single configuration, latest version
    value: bytes = parameters.get_app_config(
        name="my_configuration",
        environment="my_env",
        application="my_app",
    )
