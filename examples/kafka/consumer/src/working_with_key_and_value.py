from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.kafka import ConsumerRecords, SchemaConfig, kafka_consumer
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()

# Define schemas for both components
key_schema = """
{
    "type": "record",
    "name": "ProductKey",
    "fields": [
        {"name": "region_name", "type": "string"}
    ]
}
"""

value_schema = """
{
    "type": "record",
    "name": "User",
    "namespace": "com.example",
    "fields": [
        {"name": "name", "type": "string"},
        {"name": "age", "type": "int"}
    ]
}
"""

# Configure both key and value schemas
schema_config = SchemaConfig(
    key_schema_type="AVRO",
    key_schema=key_schema,
    value_schema_type="AVRO",
    value_schema=value_schema,
)


@kafka_consumer(schema_config=schema_config)
def lambda_handler(event: ConsumerRecords, context: LambdaContext):
    for record in event.records:
        # Access both deserialized components
        key = record.key
        value = record.value

        logger.info(f"Processing key: {key['region_name']}")
        logger.info(f"Processing value: {value['name']}")

    return {"statusCode": 200}
