from aws_lambda_powertools import Logger, Metrics
from aws_lambda_powertools.metrics import MetricUnit
from aws_lambda_powertools.utilities.kafka import ConsumerRecords, SchemaConfig, kafka_consumer
from aws_lambda_powertools.utilities.kafka.exceptions import (
    KafkaConsumerAvroSchemaParserError,
    KafkaConsumerDeserializationError,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
metrics = Metrics()

schema_config = SchemaConfig(value_schema_type="JSON")


def process_order(order):
    # Simulate processing logic
    return order


def send_to_dlq(record):
    # Simulate sending to DLQ
    logger.error("Sending to DLQ", record=record)


@kafka_consumer(schema_config=schema_config)
def lambda_handler(event: ConsumerRecords, context: LambdaContext):
    metrics.add_metric(name="TotalRecords", unit=MetricUnit.Count, value=len(list(event.records)))

    for record in event.records:
        try:
            order = record.value
            process_order(order)
            metrics.add_metric(name="ProcessedRecords", unit=MetricUnit.Count, value=1)

        except KafkaConsumerAvroSchemaParserError as exc:
            logger.error("Invalid Avro schema configuration", error=str(exc))
            metrics.add_metric(name="SchemaErrors", unit=MetricUnit.Count, value=1)
            # This requires fixing the schema - might want to raise to stop processing
            raise

        except KafkaConsumerDeserializationError as exc:
            logger.warning("Message format doesn't match schema", topic=record.topic, error=str(exc))
            metrics.add_metric(name="DeserializationErrors", unit=MetricUnit.Count, value=1)
            # Send to dead-letter queue for analysis
            send_to_dlq(record)

    return {"statusCode": 200, "metrics": metrics.serialize_metric_set()}
