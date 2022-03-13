from botocore.config import Config

from aws_lambda_powertools.utilities.idempotency import DynamoDBPersistenceLayer, IdempotencyConfig, idempotent

config = IdempotencyConfig(event_key_jmespath="body")
boto_config = Config()
persistence_layer = DynamoDBPersistenceLayer(
    table_name="IdempotencyTable",
    boto_config=boto_config,
)


@idempotent(config=config, persistence_store=persistence_layer)
def handler(event, context):
    ...
