from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent, event_source


@event_source(data_class=APIGatewayProxyEvent)
def lambda_handler(event: APIGatewayProxyEvent, context):
    if "hello" in event.path and event.http_method == "GET":
        return {"statusCode": 200, "body": f"Hello from path: {event.path}"}
    else:
        return {"statusCode": 400, "body": "No Hello from path"}
