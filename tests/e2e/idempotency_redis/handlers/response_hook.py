import os

from aws_lambda_powertools.utilities.idempotency import (
    IdempotencyConfig,
    idempotent,
)
from aws_lambda_powertools.utilities.idempotency.persistence.datarecord import (
    DataRecord,
)
from aws_lambda_powertools.utilities.idempotency.persistence.redis import RedisCachePersistenceLayer

REDIS_HOST = os.getenv("RedisEndpoint", "")
persistence_layer = RedisCachePersistenceLayer(host=REDIS_HOST, port=6379)


def my_response_hook(response: dict, idempotent_data: DataRecord) -> dict:
    # Return inserted Header data into the Idempotent Response
    response["x-response-hook"] = idempotent_data.idempotency_key

    # Must return the response here
    return response


config = IdempotencyConfig(response_hook=my_response_hook)


@idempotent(config=config, persistence_store=persistence_layer)
def lambda_handler(event, context):
    return {"message": "first_response"}
