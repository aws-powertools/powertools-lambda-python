from pydantic import BaseModel

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.kafka import ConsumerRecords, SchemaConfig, kafka_consumer
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


# Define Pydantic model for strong validation
class User(BaseModel):
    name: str
    age: int


# Configure with Avro schema and Pydantic output
schema_config = SchemaConfig(value_schema_type="JSON", value_output_serializer=User)


@kafka_consumer(schema_config=schema_config)
def lambda_handler(event: ConsumerRecords, context: LambdaContext):
    for record in event.records:
        # record.value is now a User instance
        value: User = record.value

        logger.info(f"Name: '{value.name}'")
        logger.info(f"Age: '{value.age}'")

    return {"statusCode": 200}
