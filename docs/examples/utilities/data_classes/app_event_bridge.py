from aws_lambda_powertools.utilities.data_classes import EventBridgeEvent, event_source


@event_source(data_class=EventBridgeEvent)
def lambda_handler(event: EventBridgeEvent, context):
    do_something_with(event.detail)
