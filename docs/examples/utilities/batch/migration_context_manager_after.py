from aws_lambda_powertools.utilities.batch import BatchProcessor, EventType, batch_processor


def record_handler(record):
    return_value = do_something_with(record["body"])
    return return_value


def lambda_handler(event, context):
    records = event["Records"]

    processor = BatchProcessor(event_type=EventType.SQS)

    with processor(records, record_handler):
        result = processor.process()

    return processor.response()
