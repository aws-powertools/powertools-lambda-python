from aws_lambda_powertools.utilities.data_classes import ALBEvent, event_source


@event_source(data_class=ALBEvent)
def lambda_handler(event: ALBEvent, context):
    if "lambda" in event.path and event.http_method == "GET":
        return {"statusCode": 200, "body": f"Hello from path: {event.path}"}
    else:
        return {"statusCode": 400, "body": "No Hello from path"}
