from aws_lambda_powertools.utilities.kafka_consumer.consumer_record import ConsumerRecord
from aws_lambda_powertools.utilities.kafka_consumer.kafka_consumer import kafka_consumer
from aws_lambda_powertools.utilities.kafka_consumer.schema_config import SchemaConfig

__all__ = [
    "kafka_consumer",
    "ConsumerRecord",
    "SchemaConfig",
]
