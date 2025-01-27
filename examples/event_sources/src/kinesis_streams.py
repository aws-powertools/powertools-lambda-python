import json
from typing import Any, Dict, Union

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.data_classes import KinesisStreamEvent, event_source
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


@event_source(data_class=KinesisStreamEvent)
def lambda_handler(event: KinesisStreamEvent, context: LambdaContext):
    for record in event.records:
        kinesis_record = record.kinesis

        payload: Union[Dict[str, Any], str]

        try:
            # Try to parse as JSON first
            payload = kinesis_record.data_as_json()
            logger.info("Received JSON data from Kinesis")
        except json.JSONDecodeError:
            # If JSON parsing fails, get as text
            payload = kinesis_record.data_as_text()
            logger.info("Received text data from Kinesis")

        process_data(payload)

    return {"statusCode": 200, "body": "Processed all records successfully"}


def process_data(data: Union[Dict[str, Any], str]) -> None:
    if isinstance(data, dict):
        # Handle JSON data
        logger.info(f"Processing JSON data: {data}")
        # Add your JSON processing logic here
    else:
        # Handle text data
        logger.info(f"Processing text data: {data}")
        # Add your text processing logic here
