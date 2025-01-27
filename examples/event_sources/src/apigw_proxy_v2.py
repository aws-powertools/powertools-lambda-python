from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEventV2, event_source


@event_source(data_class=APIGatewayProxyEventV2)
def lambda_handler(event: APIGatewayProxyEventV2, context):
    if "hello" in event.path and event.http_method == "POST":
        return {"statusCode": 200, "body": f"Hello from path: {event.path}"}
    else:
        return {"statusCode": 400, "body": "No Hello from path"}
