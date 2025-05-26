from aws_lambda_powertools.utilities.data_classes import SQSEvent, SQSRecord, event_source


@event_source(data_class=SQSEvent)
def lambda_handler(event: SQSEvent, context):
    # Multiple records can be delivered in a single event
    for record in event.records:
        message, message_id = process_record(record)
    return {
        "message": message,
        "message_id": message_id,
    }


def process_record(record: SQSRecord):
    message = record.body
    message_id = record.message_id
    return message, message_id
