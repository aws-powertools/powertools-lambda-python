from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.data_classes.iot_registry_event import IoTCoreAddOrRemoveFromThingGroupEvent


@event_source(data_class=IoTCoreAddOrRemoveFromThingGroupEvent)
def lambda_handler(event: IoTCoreAddOrRemoveFromThingGroupEvent, context):
    print(f"Received IoT Core event type {event.event_type}")
