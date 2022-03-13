from aws_lambda_powertools.utilities.idempotency import DynamoDBPersistenceLayer, IdempotencyConfig, idempotent

persistence_layer = DynamoDBPersistenceLayer(table_name="IdempotencyTable")
config = IdempotencyConfig(
    event_key_jmespath="body",
    expires_after_seconds=5 * 60,  # 5 minutes
)


@idempotent(config=config, persistence_store=persistence_layer)
def handler(event, context):
    ...
