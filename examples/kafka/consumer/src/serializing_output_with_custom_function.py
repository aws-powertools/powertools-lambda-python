from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.kafka import ConsumerRecords, SchemaConfig, kafka_consumer
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


# Define custom serializer
def custom_serializer(data: dict):
    del data["age"]  # Remove age key just for example
    return data


# Configure with Avro schema and function serializer
schema_config = SchemaConfig(value_schema_type="JSON", value_output_serializer=custom_serializer)


@kafka_consumer(schema_config=schema_config)
def lambda_handler(event: ConsumerRecords, context: LambdaContext):
    for record in event.records:
        # record.value now only contains the key "name"
        value = record.value

        logger.info(f"Name: '{value['name']}'")

    return {"statusCode": 200}
