import os

from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    IdempotencyConfig,
    idempotent,
)
from aws_lambda_powertools.utilities.idempotency.persistence.datarecord import (
    DataRecord,
)

TABLE_NAME = os.getenv("IdempotencyTable", "")
persistence_layer = DynamoDBPersistenceLayer(table_name=TABLE_NAME)


def my_response_hook(response: dict, idempotent_data: DataRecord) -> dict:
    # Return inserted Header data into the Idempotent Response
    response["x-response-hook"] = idempotent_data.idempotency_key

    # Must return the response here
    return response


config = IdempotencyConfig(response_hook=my_response_hook)


@idempotent(config=config, persistence_store=persistence_layer)
def lambda_handler(event, context):
    return {"message": "first_response"}
