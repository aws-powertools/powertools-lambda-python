from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent, event_source


@event_source(data_class=APIGatewayProxyEvent)
def lambda_handler(event: APIGatewayProxyEvent, context):
    if "helloworld" in event.path and event.http_method == "GET":
        do_something_with(event.body, user)
