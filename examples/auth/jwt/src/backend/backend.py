from aws_lambda_powertools.utilities.typing import LambdaContext


def lambda_handler(event: dict, context: LambdaContext):
    # API Gateway invokes this function only after the authorizer allows it.
    return {"statusCode": 200, "body": '{"orders":[]}', "headers": {"Content-Type": "application/json"}}
