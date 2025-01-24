from aws_lambda_powertools.utilities.data_classes import KafkaEvent, event_source


def do_something_with(key: str, value: str):
    print(f"key: {key}, value: {value}")


@event_source(data_class=KafkaEvent)
def lambda_handler(event: KafkaEvent, context):
    for record in event.records:
        do_something_with(record.topic, record.value)
    return "success"
