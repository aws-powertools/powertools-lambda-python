from aws_lambda_powertools.utilities.data_classes import EventBridgeEvent, event_source


@event_source(data_class=EventBridgeEvent)
def lambda_handler(event: EventBridgeEvent, context):
    detail_type = event.detail_type
    state = event.detail.get("state")

    # Do something

    return {"detail_type": detail_type, "state": state}
