from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.batch import (
    BatchProcessor,
    EventType,
    process_partial_response,
)
from aws_lambda_powertools.utilities.data_classes.kafka_event import (
    KafkaEventRecord,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

processor = BatchProcessor(event_type=EventType.Kafka)  # (1)!
tracer = Tracer()
logger = Logger()


@tracer.capture_method
def record_handler(record: KafkaEventRecord):
    logger.info(f"Processing record from topic: {record.topic}, partition: {record.partition}, offset: {record.offset}")
    payload: dict = record.json_value
    logger.info(payload)


@logger.inject_lambda_context
@tracer.capture_lambda_handler
def lambda_handler(event, context: LambdaContext):
    return process_partial_response(event=event, record_handler=record_handler, processor=processor, context=context)
