from aws_lambda_powertools.utilities.kafka import ConsumerRecords, SchemaConfig, kafka_consumer
from aws_lambda_powertools.utilities.typing import LambdaContext

schema_config = SchemaConfig(value_schema_type="JSON")


@kafka_consumer(schema_config=schema_config)
def lambda_handler(event: ConsumerRecords, context: LambdaContext):
    return {"statusCode": 200, "processed": len(list(event.records))}
