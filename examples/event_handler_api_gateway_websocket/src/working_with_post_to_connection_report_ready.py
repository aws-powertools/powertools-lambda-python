# A separate Lambda function, in a different execution environment from the WebSocket
# resolver — invoked when the work completes, e.g. as the final state of a Step Functions
# workflow. The connection store is the only thing the two functions share.

import json

import boto3
import my_connection_store
from botocore.config import Config

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()
boto_config = Config(connect_timeout=3, read_timeout=5, retries={"total_max_attempts": 2})


def management_client_for(callback_url: str):
    return boto3.client("apigatewaymanagementapi", endpoint_url=callback_url, config=boto_config)


def lambda_handler(event: dict, context: LambdaContext) -> None:
    connection_id = event["connectionId"]
    callback_url = my_connection_store.get_callback_url(connection_id)  # (1)!

    client = management_client_for(callback_url)
    try:
        client.post_to_connection(ConnectionId=connection_id, Data=json.dumps(event["report"]).encode())
    except client.exceptions.GoneException:  # (2)!
        logger.info("Client disconnected before the report was ready", connection_id=connection_id)
        my_connection_store.delete(connection_id)
