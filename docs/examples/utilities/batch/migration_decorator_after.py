import json

from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, batch_processor

processor = BatchProcessor(event_type=EventType.SQS)


def record_handler(record):
    return do_something_with(record["body"])


@batch_processor(record_handler=record_handler, processor=processor)
def lambda_handler(event, context):
    return processor.response()
