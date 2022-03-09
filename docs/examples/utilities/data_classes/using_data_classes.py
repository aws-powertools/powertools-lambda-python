from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent


def lambda_handler(event: dict, context):
    event = APIGatewayProxyEvent(event)
    if "helloworld" in event.path and event.http_method == "GET":
        do_something_with(event.body, user)
