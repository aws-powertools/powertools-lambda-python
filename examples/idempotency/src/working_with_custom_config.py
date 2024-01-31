from botocore.config import Config

from aws_lambda_powertools.utilities.idempotency import (
    DynamoDBPersistenceLayer,
    IdempotencyConfig,
    idempotent,
)
from aws_lambda_powertools.utilities.typing import LambdaContext

# See: https://botocore.amazonaws.com/v1/documentation/api/latest/reference/config.html#botocore-config
boto_config = Config()

persistence_layer = DynamoDBPersistenceLayer(table_name="IdempotencyTable", boto_config=boto_config)

config = IdempotencyConfig(event_key_jmespath="body")


@idempotent(persistence_store=persistence_layer, config=config)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    return event
