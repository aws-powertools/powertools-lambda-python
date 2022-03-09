from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEventV2, event_source


@event_source(data_class=APIGatewayProxyEventV2)
def lambda_handler(event: APIGatewayProxyEventV2, context):
    if "helloworld" in event.path and event.http_method == "POST":
        do_something_with(event.json_body, event.query_string_parameters)
