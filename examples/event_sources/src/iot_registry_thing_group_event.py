from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.data_classes.iot_registry_event import IoTCoreThingGroupEvent


@event_source(data_class=IoTCoreThingGroupEvent)
def lambda_handler(event: IoTCoreThingGroupEvent, context):
    print(f"Received IoT Core event type {event.event_type}")
