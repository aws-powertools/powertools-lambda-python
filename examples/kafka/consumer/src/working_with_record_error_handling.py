from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.kafka import ConsumerRecords, SchemaConfig, kafka_consumer
from aws_lambda_powertools.utilities.kafka.exceptions import KafkaConsumerDeserializationError
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()

schema_config = SchemaConfig(value_schema_type="JSON")


def process_customer_data(customer_data: dict):
    # Simulate processing logic
    if customer_data.get("name") == "error":
        raise ValueError("Simulated processing error")


@kafka_consumer(schema_config=schema_config)
def lambda_handler(event: ConsumerRecords, context: LambdaContext):
    successful_records = 0
    failed_records = 0

    for record in event.records:
        try:
            # Process each record individually to isolate failures
            process_customer_data(record.value)
            successful_records += 1

        except KafkaConsumerDeserializationError as e:
            failed_records += 1
            logger.error(
                "Failed to deserialize Kafka message",
                extra={"topic": record.topic, "partition": record.partition, "offset": record.offset, "error": str(e)},
            )
            # Optionally send to DLQ or error topic

        except Exception as e:
            failed_records += 1
            logger.error("Error processing Kafka message", extra={"error": str(e), "topic": record.topic})

    return {"statusCode": 200, "body": f"Processed {successful_records} records successfully, {failed_records} failed"}
