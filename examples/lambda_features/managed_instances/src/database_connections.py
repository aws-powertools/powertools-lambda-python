import boto3

from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext

logger = Logger()

# Each process creates its own client
# This is fine - boto3 clients are not thread-safe anyway
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table("MyTable")


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    # Each process has its own connection
    response = table.get_item(Key={"pk": event["id"]})
    return {"statusCode": 200, "body": response.get("Item")}
