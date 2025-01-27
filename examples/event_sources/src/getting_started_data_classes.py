from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent


def lambda_handler(event: dict, context):
    api_event = APIGatewayProxyEvent(event)
    if "hello" in api_event.path and api_event.http_method == "GET":
        return {"statusCode": 200, "body": f"Hello from path: {api_event.path}"}
    else:
        return {"statusCode": 400, "body": "No Hello from path"}
