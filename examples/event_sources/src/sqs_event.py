from aws_lambda_powertools.utilities.data_classes import SQSEvent, event_source


@event_source(data_class=SQSEvent)
def lambda_handler(event: SQSEvent, context):
    # Multiple records can be delivered in a single event
    for record in event.records:
        message = record.body
        message_id = record.message_id
    return {
        "message": message,
        "message_id": message_id,
    }
