from aws_lambda_powertools.utilities.data_classes import LambdaFunctionUrlEvent, event_source


@event_source(data_class=LambdaFunctionUrlEvent)
def lambda_handler(event: LambdaFunctionUrlEvent, context):
    if event.request_context.http.method == "GET":
        return {"statusCode": 200, "body": "Hello World!"}
