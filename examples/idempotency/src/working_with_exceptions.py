import requests

from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    IdempotencyConfig,
    idempotent_function,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

persistence_layer = DynamoDBPersistenceLayer(table_name="IdempotencyTable")

config = IdempotencyConfig()


def lambda_handler(event: dict, context: LambdaContext):
    # If an exception is raised here, no idempotent record will ever get created as the
    # idempotent function does not get called
    try:
        endpoint = "https://jsonplaceholder.typicode.com/comments/"  # change this endpoint to force an exception
        requests.get(endpoint)
    except Exception as exc:
        return str(exc)

    call_external_service(data={"user": "user1", "id": 5})

    # This exception will not cause the idempotent record to be deleted, since it
    # happens after the decorated function has been successfully called
    raise Exception


@idempotent_function(data_keyword_argument="data", config=config, persistence_store=persistence_layer)
def call_external_service(data: dict):
    result: requests.Response = requests.post(
        "https://jsonplaceholder.typicode.com/comments/",
        json={"user": data["user"], "transaction_id": data["id"]},
    )
    return result.json()
