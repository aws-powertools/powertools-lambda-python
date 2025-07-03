from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.idempotency import DynamoDBPersistenceLayer, IdempotencyConfig, idempotent_function
from aws_lambda_powertools.utilities.kafka import ConsumerRecords, SchemaConfig, kafka_consumer
from aws_lambda_powertools.utilities.typing import LambdaContext

# Configure persistence layer for idempotency
persistence_layer = DynamoDBPersistenceLayer(table_name="IdempotencyTable")
logger = Logger()
idempotency_config = IdempotencyConfig()

# Configure Kafka schema
avro_schema = """
{
    "type": "record",
    "name": "Payment",
    "fields": [
        {"name": "payment_id", "type": "string"},
        {"name": "customer_id", "type": "string"},
        {"name": "amount", "type": "double"},
        {"name": "status", "type": "string"}
    ]
}
"""

schema_config = SchemaConfig(value_schema_type="AVRO", value_schema=avro_schema)


@kafka_consumer(schema_config=schema_config)
def lambda_handler(event: ConsumerRecords, context: LambdaContext):
    idempotency_config.register_lambda_context(context)

    for record in event.records:
        # Process each message with idempotency protection
        process_payment(payment=record.value, topic=record.topic, partition=record.partition, offset=record.offset)

    return {"statusCode": 200}


@idempotent_function(
    data_keyword_argument="payment",
    persistence_store=persistence_layer,
)
def process_payment(payment, topic, partition, offset):
    """Process a payment exactly once"""
    logger.info(f"Processing payment {payment['payment_id']} from {topic}-{partition}-{offset}")

    # Execute payment logic

    return {"success": True, "payment_id": payment["payment_id"]}
