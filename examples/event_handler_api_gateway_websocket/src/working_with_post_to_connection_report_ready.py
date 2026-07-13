# A separate Lambda function, in a different execution environment from the WebSocket
# resolver — invoked when the work completes, e.g. as the final state of a Step Functions
# workflow. The connection store is the only thing the two functions share.

import json

import boto3
import my_connection_store

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()


def lambda_handler(event: dict, context: LambdaContext) -> None:
    connection_id = event["connectionId"]
    callback_url = my_connection_store.get_callback_url(connection_id)  # (1)!

    client = boto3.client("apigatewaymanagementapi", endpoint_url=callback_url)
    try:
        client.post_to_connection(ConnectionId=connection_id, Data=json.dumps(event["report"]).encode())
    except client.exceptions.GoneException:  # (2)!
        logger.info("Client disconnected before the report was ready", connection_id=connection_id)
        my_connection_store.delete(connection_id)
