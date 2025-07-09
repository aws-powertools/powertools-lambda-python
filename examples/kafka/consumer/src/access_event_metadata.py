from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.kafka import ConsumerRecords, SchemaConfig, kafka_consumer
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()

# Define Avro schema
avro_schema = """
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

schema_config = SchemaConfig(
    value_schema_type="AVRO",
    value_schema=avro_schema,
)


@kafka_consumer(schema_config=schema_config)
def lambda_handler(event: ConsumerRecords, context: LambdaContext):
    for record in event.records:
        # Log record coordinates for tracing
        logger.info(f"Processing message from topic '{record.topic}'")
        logger.info(f"Partition: {record.partition}, Offset: {record.offset}")
        logger.info(f"Produced at: {record.timestamp}")

        # Process message headers
        logger.info(f"Headers: {record.headers}")

        # Access the Avro deserialized message content
        value = record.value
        logger.info(f"Deserialized value: {value['name']}")

        # For debugging, you can access the original raw data
        logger.info(f"Raw message: {record.original_value}")

    return {"statusCode": 200}
