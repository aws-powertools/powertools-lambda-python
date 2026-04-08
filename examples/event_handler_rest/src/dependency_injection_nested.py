import os
from typing import Any

import boto3
from typing_extensions import Annotated

from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.event_handler.depends import Depends
from aws_lambda_powertools.utilities.typing import LambdaContext

app = APIGatewayHttpResolver()


def get_dynamodb_resource():
    return boto3.resource("dynamodb")


def get_orders_table(dynamodb: Annotated[Any, Depends(get_dynamodb_resource)]):
    return dynamodb.Table(os.environ["ORDERS_TABLE"])


def get_users_table(dynamodb: Annotated[Any, Depends(get_dynamodb_resource)]):
    return dynamodb.Table(os.environ["USERS_TABLE"])


@app.get("/orders/<user_id>")
def get_user_orders(
    user_id: str,
    orders_table: Annotated[Any, Depends(get_orders_table)],
    users_table: Annotated[Any, Depends(get_users_table)],
):
    user = users_table.get_item(Key={"pk": user_id})["Item"]
    orders = orders_table.query(KeyConditionExpression="pk = :uid", ExpressionAttributeValues={":uid": user_id})
    return {"user": user["name"], "orders": orders["Items"]}


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
