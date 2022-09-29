from aws_lambda_powertools.utilities import parameters


def lambda_handler(event, context):
    # Retrieve a single parameter
    value = parameters.get_parameter("sample_string")

    return {"value": value}
