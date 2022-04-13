from aws_lambda_powertools.utilities.idempotency import DynamoDBPersistenceLayer, IdempotencyConfig, idempotent

persistence_layer = DynamoDBPersistenceLayer(table_name="IdempotencyTable")
config = IdempotencyConfig(
    event_key_jmespath="body",
    use_local_cache=True,
)


@idempotent(config=config, persistence_store=persistence_layer)
def handler(event, context):
    ...
