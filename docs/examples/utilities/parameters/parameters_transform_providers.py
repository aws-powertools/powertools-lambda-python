from aws_lambda_powertools.utilities import parameters

ssm_provider = parameters.SSMProvider()


def handler(event, context):
    # Transform a JSON string
    value_from_json = ssm_provider.get("/my/json/parameter", transform="json")

    # Transform a Base64 encoded string
    value_from_binary = ssm_provider.get("/my/binary/parameter", transform="binary")
