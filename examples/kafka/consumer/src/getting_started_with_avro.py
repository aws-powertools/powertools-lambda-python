from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.kafka import ConsumerRecords, SchemaConfig, kafka_consumer
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()

# Define the Avro schema
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

# Configure schema
schema_config = SchemaConfig(
    value_schema_type="AVRO",
    value_schema=avro_schema,
)


@kafka_consumer(schema_config=schema_config)
def lambda_handler(event: ConsumerRecords, context: LambdaContext):
    for record in event.records:
        user = record.value  # Dictionary from avro message

        logger.info(f"Processing user: {user['name']}, age {user['age']}")

    return {"statusCode": 200}
