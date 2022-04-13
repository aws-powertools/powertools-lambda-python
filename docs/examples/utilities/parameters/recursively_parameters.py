from aws_lambda_powertools.utilities import parameters


def handler(event, context):
    # Retrieve a single parameter
    value = parameters.get_parameter("/my/parameter")

    # Retrieve multiple parameters from a path prefix recursively
    # This returns a dict with the parameter name as key
    values = parameters.get_parameters("/my/path/prefix")
    for k, v in values.items():
        print(f"{k}: {v}")
