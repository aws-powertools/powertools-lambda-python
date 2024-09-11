import os

from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    IdempotencyConfig,
    idempotent,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

table = os.getenv("IDEMPOTENCY_TABLE", "")
persistence_layer = DynamoDBPersistenceLayer(table_name=table)
config = IdempotencyConfig(
    event_key_jmespath="powertools_json(body)",
    # by default, it holds 256 items in a Least-Recently-Used (LRU) manner
    use_local_cache=True,  # (1)!
)


@idempotent(config=config, persistence_store=persistence_layer)
def lambda_handler(event, context: LambdaContext):
    return event
