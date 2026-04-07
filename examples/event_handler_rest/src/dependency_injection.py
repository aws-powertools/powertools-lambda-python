import os
from typing import Any

import boto3
from typing_extensions import Annotated

from aws_lambda_powertools.event_handler import APIGatewayHttpResolver
from aws_lambda_powertools.event_handler.depends import Depends
from aws_lambda_powertools.utilities.typing import LambdaContext

app = APIGatewayHttpResolver()


def get_dynamodb_table():
    dynamodb = boto3.resource("dynamodb")
    return dynamodb.Table(os.environ["TABLE_NAME"])


@app.get("/orders")
def list_orders(table: Annotated[Any, Depends(get_dynamodb_table)]):
    return table.scan()["Items"]


@app.post("/orders")
def create_order(table: Annotated[Any, Depends(get_dynamodb_table)]):
    order = app.current_event.json_body
    table.put_item(Item=order)
    return {"message": "Order created"}


def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return app.resolve(event, context)
