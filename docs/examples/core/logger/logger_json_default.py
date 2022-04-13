from aws_lambda_powertools import Logger


def custom_json_default(value):
    return f"<non-serializable: {type(value).__name__}>"


class Unserializable:
    pass


logger = Logger(service="payment", json_default=custom_json_default)


def handler(event, context):
    logger.info(Unserializable())
