from aws_lambda_powertools.utilities import parameters


def handler(event, context):
    # Retrieve a single parameter
    value = parameters.get_parameter("my-parameter-name")
    return {"message": value}
