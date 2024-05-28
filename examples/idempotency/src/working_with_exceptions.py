import os

import requests

from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    IdempotencyConfig,
    idempotent_function,
)
from aws_lambda_powertools.utilities.idempotency.exceptions import IdempotencyPersistenceLayerError
from aws_lambda_powertools.utilities.typing import LambdaContext

table = os.getenv("IDEMPOTENCY_TABLE")
persistence_layer = DynamoDBPersistenceLayer(table_name=table)

config = IdempotencyConfig()


@idempotent_function(data_keyword_argument="data", config=config, persistence_store=persistence_layer)
def call_external_service(data: dict):
    # Any exception raised will lead to idempotency record to be deleted
    result: requests.Response = requests.post(
        "https://jsonplaceholder.typicode.com/comments/",
        json=data,
    )
    return result.json()


def lambda_handler(event: dict, context: LambdaContext):
    try:
        call_external_service(data=event)
    except IdempotencyPersistenceLayerError as e:
        # No idempotency, but you can decide to error differently.
        raise RuntimeError(f"Oops, can't talk to persistence layer. Permissions? error: {e}")

    # This exception will not impact the idempotency of 'call_external_service'
    # because it happens in isolation, or outside their scope.
    raise SyntaxError("Oops, this shouldn't be here.")
