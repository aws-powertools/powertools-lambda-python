from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.kafka import ConsumerRecords, SchemaConfig, kafka_consumer
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()

# Configure only value schema
schema_config = SchemaConfig(value_schema_type="JSON")


@kafka_consumer(schema_config=schema_config)
def lambda_handler(event: ConsumerRecords, context: LambdaContext):
    for record in event.records:
        # Key remains as string (if present)
        if record.key is not None:
            logger.info(f"Message key: {record.key}")

        # Value is deserialized as JSON
        value = record.value
        logger.info(f"Order #{value['order_id']} - Total: ${value['total']}")

    return {"statusCode": 200}
