from datetime import datetime

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.kafka import ConsumerRecords, SchemaConfig, kafka_consumer
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()

# Define schema that matches Java producer
avro_schema = """
{
    "namespace": "com.example.orders",
    "type": "record",
    "name": "OrderEvent",
    "fields": [
        {"name": "orderId", "type": "string"},
        {"name": "customerId", "type": "string"},
        {"name": "totalAmount", "type": "double"},
        {"name": "orderDate", "type": "long", "logicalType": "timestamp-millis"}
    ]
}
"""


# Configure schema with field name normalization for Python style
def normalize_field_name(data: dict):
    data["order_id"] = data["orderId"]
    data["customer_id"] = data["customerId"]
    data["total_amount"] = data["totalAmount"]
    data["order_date"] = datetime.fromtimestamp(data["orderDate"] / 1000)
    return data


schema_config = SchemaConfig(
    value_schema_type="AVRO",
    value_schema=avro_schema,
    value_output_serializer=normalize_field_name,
)


@kafka_consumer(schema_config=schema_config)
def lambda_handler(event: ConsumerRecords, context: LambdaContext):
    for record in event.records:
        order = record.value  # OrderProcessor instance
        logger.info(f"Processing order {order['order_id']}")
