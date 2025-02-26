from aws_lambda_powertools.utilities.data_classes import event_source
from aws_lambda_powertools.utilities.data_classes.iot_registry_event import IoTCoreThingEvent


@event_source(data_class=IoTCoreThingEvent)
def lambda_handler(event: IoTCoreThingEvent, context):
    print(f"Received IoT Core event type {event.event_type}")
