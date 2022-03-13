from aws_lambda_powertools.utilities import parameters


def handler(event, context):
    value_from_json = parameters.get_parameter("/my/json/parameter", transform="json")
