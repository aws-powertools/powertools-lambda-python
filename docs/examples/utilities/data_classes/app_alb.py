from aws_lambda_powertools.utilities.data_classes import ALBEvent, event_source


@event_source(data_class=ALBEvent)
def lambda_handler(event: ALBEvent, context):
    if "helloworld" in event.path and event.http_method == "POST":
        do_something_with(event.json_body, event.query_string_parameters)
