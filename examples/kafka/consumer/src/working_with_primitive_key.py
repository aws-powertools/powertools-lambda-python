from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.kafka import ConsumerRecords, SchemaConfig, kafka_consumer
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()

# Only configure value schema
schema_config = SchemaConfig(value_schema_type="JSON")


@kafka_consumer(schema_config=schema_config)
def lambda_handler(event: ConsumerRecords, context: LambdaContext):
    for record in event.records:
        # Key is automatically decoded as UTF-8 string
        key = record.key

        # Value is deserialized as JSON
        value = record.value

        logger.info(f"Processing key: {key}")
        logger.info(f"Processing value: {value['name']}")

    return {"statusCode": 200}
