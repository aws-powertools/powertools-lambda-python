from aws_lambda_powertools.utilities.data_classes import KinesisStreamEvent, event_source


@event_source(data_class=KinesisStreamEvent)
def lambda_handler(event: KinesisStreamEvent, context):
    kinesis_record = next(event.records).kinesis

    # if data was delivered as text
    data = kinesis_record.data_as_text()

    # if data was delivered as json
    data = kinesis_record.data_as_json()

    do_something_with(data)
