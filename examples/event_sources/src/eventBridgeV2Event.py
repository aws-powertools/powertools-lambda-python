from aws_lambda_powertools.utilities.data_classes import EventBridgeV2Event, event_source


@event_source(data_class=EventBridgeV2Event)
def lambda_handler(event: EventBridgeV2Event, context):
    for record in event.records:
        if record.system_metadata.delivery_type == "REPLAY":
            continue

        # Do something with record.data, or record.detail when published with PutEvents
        print(record.system_metadata.event_id, record.data)
