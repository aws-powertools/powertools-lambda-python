from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.kafka import ConsumerRecords, kafka_consumer
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


@kafka_consumer
def lambda_handler(event: ConsumerRecords, context: LambdaContext):
    for record in event.records:
        # Key is automatically decoded as UTF-8 string
        key = record.key

        # Value is automatically decoded as UTF-8 string
        value = record.value

        logger.info(f"Processing key: {key}")
        logger.info(f"Processing value: {value}")

    return {"statusCode": 200}
