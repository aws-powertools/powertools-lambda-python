from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.kafka import ConsumerRecords, SchemaConfig, kafka_consumer
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()

# Define schemas for key
key_schema = """
{
    "type": "record",
    "name": "ProductKey",
    "fields": [
        {"name": "region_name", "type": "string"}
    ]
}
"""

# Configure key schema
schema_config = SchemaConfig(
    key_schema_type="AVRO",
    key_schema=key_schema,
)


@kafka_consumer(schema_config=schema_config)
def lambda_handler(event: ConsumerRecords, context: LambdaContext):
    for record in event.records:
        # Access deserialized key
        key = record.key

        logger.info(f"Processing key: {key}")

    return {"statusCode": 200}
