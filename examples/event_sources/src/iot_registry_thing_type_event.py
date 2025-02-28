from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.data_classes.iot_registry_event import IoTCoreThingTypeEvent


@event_source(data_class=IoTCoreThingTypeEvent)
def lambda_handler(event: IoTCoreThingTypeEvent, context):
    print(f"Received IoT Core event type {event.event_type}")
